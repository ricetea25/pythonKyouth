

import os
import json
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from pathlib import Path


class JobListing(BaseModel):
	source_id: str
	job_title: str
	company: str
	description: str

# def extract_data(html_content):
# 	soup = BeautifulSoup(html_content, 'html.parser')

# 	return soup

def process_all_html(input_dir, output_dir):
	os.makedirs(output_dir, exist_ok=True)

	html_files = list(Path(input_dir).glob("*.html"))
	processed_count = 0
	skipped_count = 0

	print("🥈 Silver:...")

	for html_path in html_files:
		with open(html_path, 'r', encoding='utf-8') as f:
			soup = BeautifulSoup(f, 'html.parser')

		try:
			# Extract source_id from og:url
			# blabla/url/<source_id>
			og_url = soup.find("meta", property="og:url")
			source_id = og_url['content'].rstrip('/').split('/')[-1] if og_url else None

			# Extract Fields
			job_title_node = soup.find(attrs={"data-automation": "job-detail-title"}) or \
			soup.find("h1") or \
			soup.find(attrs={"data-job-title": True})

			company_node = soup.find("span", attrs={"data-automation": "advertiser-name"}) or \
			soup.find(attrs={"data-company": True})

			desc_node = soup.find(attrs={"data-automation": "jobAdDetails"}) or \
			soup.find(id="job-description")

			# Extract text if node was found
			job_title = job_title_node.get_text(strip=True) if job_title_node else None
			print(job_title)
			company = company_node.get_text(strip=True) if company_node else None
			# print(company)
			description = desc_node.get_text(separator=" ", strip=True) if desc_node else None
			# print(description)

			# error messages if missing
			missing = []
			if not job_title: missing.append("job_title")
			if not company: missing.append("company")
			if not description: missing.append("description")

			if missing:
				for field in missing:
					print(f"⚠️ Missing {field} in: {html_path.name}")
				skipped_count += 1
				continue

			# Create Pydantic Object basically like a class
			job_data = JobListing(
				source_id=str(source_id),
				job_title=job_title,
				company=company,
				description=description
			)

			# Save to JSON overwrites existing path names
			output_file = Path(output_dir) / f"{html_path.stem}.json"
			with open(output_file, 'w', encoding='utf-8') as jf:
				json.dump(job_data.model_dump(), jf, indent=2, ensure_ascii=False)
			
			print(f"✅ Processed: {html_path.name}")
			processed_count += 1

		except Exception as e:
			print(f"❌ Error processing {html_path.name}: {e}")
			skipped_count += 1

	print(f"\n📊 Silver Summary:\nTotal: {len(html_files)} | Processed: {processed_count} | Skipped: {skipped_count}")