from pathlib import Path
import email
from email import policy


def decode_mhtml_to_html(mhtml_path):
    with open(mhtml_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    for part in msg.walk():
        if part.get_content_type() == "text/html":

            payload = part.get_payload(decode=True)
            charset = part.get_content_charset() or 'utf-8'
            return payload.decode(charset, errors='replace')
        
    return None

def ingest_all_mhtml(input_dir, output_dir):
    for mhtml_file in Path(input_dir).glob("*mhtml"):
        html_str = decode_mhtml_to_html(mhtml_file)

        output_path = Path(output_dir) / f"{mhtml_file.stem}.html"
        output_path.write_text(html_str, encoding='utf-8')


