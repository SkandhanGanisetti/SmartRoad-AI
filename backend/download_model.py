"""Download a user-supplied RDD YOLO checkpoint from Hugging Face."""
import argparse
from pathlib import Path
from huggingface_hub import hf_hub_download
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description='Download a fine-tuned RDD2022 YOLO .pt checkpoint')
parser.add_argument('--repo',required=True,help='Hugging Face repository, e.g. owner/repository')
parser.add_argument('--filename',default='best.pt',help='Checkpoint filename in that repository')
args=parser.parse_args(); destination=ROOT/'ml'/'best.pt';destination.parent.mkdir(exist_ok=True)
source=hf_hub_download(repo_id=args.repo,filename=args.filename);destination.write_bytes(Path(source).read_bytes());print(f'Model saved to {destination}')
