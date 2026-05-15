from pathlib import Path
import email
from email import policy


def decode_mhtml_to_html(mhtml_path):
    with open(mhtml_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            
            # extracts the raw binary, stripping away the email transport layer
            payload = part.get_payload(decode=True)
            # # utf-8 is safety net if get_content_charset returns null
            charset = part.get_content_charset() or 'utf-8'
            # change byte objects into readable character
            return payload.decode(charset, errors='replace')
        
    return None

def ingest_all_mhtml(input_dir, output_dir):
    # .glob() is a methos used to find files and folders
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    mhtml_files = list(Path(input_dir).glob("*.mhtml"))
    extracted_count = 0
    failed_count = 0

    print("🥉 Bronze:...")

    for mhtml_file in mhtml_files:
        html_str = decode_mhtml_to_html(mhtml_file)

        if not html_str:
            print(f"⚠️ No HTML content found in: {mhtml_file.name}")
            failed_count += 1
            continue

        output_path = Path(output_dir) / f"{mhtml_file.stem}.html"
        output_path.write_text(html_str, encoding='utf-8')
        print(f"✅ Extracted: {mhtml_file.name}")
        extracted_count += 1

    print(
        "\n📊 Bronze Summary:\n"
        f"Total: {len(mhtml_files)} | Extracted: {extracted_count} | Failed: {failed_count}"
    )


