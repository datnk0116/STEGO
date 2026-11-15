from fractions import Fraction
import numpy as np
import soundfile as sf
from scipy.signal import correlate, correlation_lags, resample_poly

def _overlap(a, b, lag):
    a0, b0 = max(lag, 0), max(-lag, 0)
    n = min(len(a)-a0, len(b)-b0)
    if n <= 0: raise ValueError('no target/reference overlap')
    return a[a0:a0+n], b[b0:b0+n], a0

def _align(target, sr, reference, ref_sr):
    if ref_sr != sr:
        ratio = Fraction(sr, ref_sr).limit_denominator(100000)
        reference = resample_poly(reference, ratio.numerator, ratio.denominator, axis=0)
    if target.shape[1] != reference.shape[1]:
        target, reference = target.mean(axis=1, keepdims=True), reference.mean(axis=1, keepdims=True)
    t, r = target.mean(axis=1), reference.mean(axis=1)
    factor = max(1, round(sr/4000))
    td, rd = resample_poly(t, 1, factor), resample_poly(r, 1, factor)
    td, rd = td-td.mean(), rd-rd.mean()
    corr = correlate(td, rd, mode='full', method='fft')
    lags = correlation_lags(len(td), len(rd), mode='full')
    coarse = int(lags[np.argmax(np.abs(corr))])*factor
    best, score = coarse, -1.0
    for lag in range(coarse-factor, coarse+factor+1):
        try: x, y, _ = _overlap(target, reference, lag)
        except ValueError: continue
        x, y = x.mean(axis=1), y.mean(axis=1)
        x, y = x-x.mean(), y-y.mean()
        den = np.linalg.norm(x)*np.linalg.norm(y)
        s = abs(float(np.dot(x,y)/den)) if den else 0.0
        if s > score: best, score = lag, s
    x, y, start = _overlap(target, reference, best)
    return x, y, {'lag_samples': best, 'correlation': score, 'target_start_sample': start}

def decode_sleepy_alarm(path, reference_path=None, carrier=8000.0, baud=50.0, duration=7.0):
    target, sr = sf.read(path, always_2d=True, dtype='float64')
    signal, alignment = target, None
    if reference_path:
        ref, ref_sr = sf.read(reference_path, always_2d=True, dtype='float64')
        x, y, alignment = _align(target, sr, ref, ref_sr)
        prefix = target[:alignment['target_start_sample']]
        if target.shape[1] != ref.shape[1]: prefix = prefix.mean(axis=1, keepdims=True)
        signal = np.concatenate((prefix, x-y), axis=0)
    if baud <= 0 or carrier <= 0 or carrier >= sr/2: raise ValueError('invalid baud/carrier')
    channel = signal[:,0]
    sps, count = sr/baud, round(duration*baud)
    levels=[]
    for i in range(count):
        a,b=round(i*sps),round((i+1)*sps)
        if b>len(channel): break
        z=channel[a:b]
        if len(z)<8: break
        phase=2*np.pi*carrier*np.arange(a,b)/sr
        z=z-z.mean()
        levels.append(float(np.hypot(2*np.dot(z,np.cos(phase))/len(z),2*np.dot(z,np.sin(phase))/len(z))) )
    if len(levels)!=count: raise ValueError(f'expected {count} symbols, measured {len(levels)}')
    values=np.asarray(levels); centers=np.quantile(values,[.05,.5,.95])
    for _ in range(100):
        labels=np.argmin(np.abs(values[:,None]-centers[None,:]),axis=1)
        new=np.array([values[labels==k].mean() if np.any(labels==k) else centers[k] for k in range(3)])
        new.sort()
        if np.allclose(new,centers,rtol=1e-7,atol=1e-12): centers=new; break
        centers=new
    labels=np.argmin(np.abs(values[:,None]-centers[None,:]),axis=1)
    if len(np.unique(labels))!=3: raise ValueError('could not separate three ASK levels')
    symbols=[{0:' ',1:'0',2:'1'}[int(x)] for x in labels]
    chunks=[]; current=[]
    for bit in symbols:
        if bit==' ':
            if current: chunks.append(''.join(current)); current=[]
        else: current.append(bit)
    if current: chunks.append(''.join(current))
    errors=[]; chars=[]
    for i,bits in enumerate(chunks):
        if len(bits)!=8: errors.append({'byte_index':i,'bits':bits})
        else: chars.append(chr(int(bits,2)))
    text=''.join(chars)
    valid=len(chunks)==39 and not errors and len(text)==39 and text.startswith('ictf{') and text.endswith('}')
    return {'decoded_text':text,'format_valid':valid,'symbol_count':len(levels),'separator_count':symbols.count(' '),'reference_assisted':reference_path is not None,'alignment':alignment,'errors':errors,'amplitude_centers':centers.tolist()}
