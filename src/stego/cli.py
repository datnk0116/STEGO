import argparse, json
from .image import decode_blue3
from .audio import decode_sleepy_alarm
def main():
    p=argparse.ArgumentParser(description='Offline steganography challenge decoders')
    s=p.add_subparsers(dest='challenge',required=True)
    i=s.add_parser('blue3'); i.add_argument('input')
    a=s.add_parser('sleepy-alarm'); a.add_argument('input'); a.add_argument('--reference')
    x=p.parse_args()
    result=decode_blue3(x.input) if x.challenge=='blue3' else decode_sleepy_alarm(x.input,x.reference)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result['format_valid'] else 2
