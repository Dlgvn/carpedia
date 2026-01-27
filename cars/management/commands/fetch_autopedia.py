import re
import requests
from django.core.management.base import BaseCommand
from cars.models import Car


class Command(BaseCommand):
    help = 'Fetch car data from Autopedia Fandom wiki'

    BASE_URL = 'https://autopedia.fandom.com/api.php'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of pages to fetch (0 for all)',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        self.stdout.write('Fetching pages from Autopedia Fandom wiki...')

        pages = self.fetch_all_pages(limit)
        self.stdout.write(f'Found {len(pages)} pages to process')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for i, page in enumerate(pages, 1):
            page_id = page['pageid']
            title = page['title']

            # Skip non-car pages (categories, templates, etc.)
            if ':' in title or title.startswith('User'):
                skipped_count += 1
                continue

            # Check if already exists
            existing = Car.objects.filter(wiki_page_id=page_id).first()

            # Fetch page content
            content = self.fetch_page_content(title)
            if not content:
                skipped_count += 1
                continue

            # Parse car data from wiki content
            car_data = self.parse_car_data(title, content)
            if not car_data.get('brand'):
                skipped_count += 1
                continue

            car_data['wiki_page_id'] = page_id

            if existing:
                for key, value in car_data.items():
                    if value:  # Only update non-empty values
                        setattr(existing, key, value)
                existing.save()
                updated_count += 1
            else:
                Car.objects.create(**car_data)
                created_count += 1

            # Progress indicator
            if i % 50 == 0:
                self.stdout.write(f'Processed {i}/{len(pages)} pages...')

        self.stdout.write(self.style.SUCCESS(
            f'Done! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'
        ))

    def fetch_all_pages(self, limit=0):
        """Fetch all pages using pagination."""
        pages = []
        apcontinue = None

        while True:
            params = {
                'action': 'query',
                'list': 'allpages',
                'aplimit': 500,
                'format': 'json',
            }
            if apcontinue:
                params['apcontinue'] = apcontinue

            try:
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.stderr.write(f'Error fetching pages: {e}')
                break

            batch = data.get('query', {}).get('allpages', [])
            pages.extend(batch)

            self.stdout.write(f'Fetched {len(pages)} page titles...')

            if limit and len(pages) >= limit:
                pages = pages[:limit]
                break

            # Check for continuation
            if 'continue' in data:
                apcontinue = data['continue'].get('apcontinue')
            else:
                break

        return pages

    def fetch_page_content(self, title):
        """Fetch the wikitext content of a page."""
        params = {
            'action': 'parse',
            'page': title,
            'format': 'json',
            'prop': 'wikitext',
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('parse', {}).get('wikitext', {}).get('*', '')
        except requests.RequestException:
            return None

    def parse_car_data(self, title, content):
        """Parse car specs from MediaWiki content."""
        data = {
            'name': '',
            'brand': '',
            'year': None,
            'description': '',
            'engine': '',
            'horsepower': None,
            'top_speed': None,
            'acceleration': None,
        }

        # Try to extract brand and name from title
        # Common formats: "Brand Model", "Brand Model (Year)", "Year Brand Model"
        title_clean = re.sub(r'\s*\([^)]*\)\s*', ' ', title).strip()
        parts = title_clean.split()

        if parts:
            # Check if first part is a year
            if parts[0].isdigit() and len(parts[0]) == 4:
                data['year'] = int(parts[0])
                data['brand'] = parts[1] if len(parts) > 1 else ''
                data['name'] = ' '.join(parts[2:]) if len(parts) > 2 else ''
            else:
                data['brand'] = parts[0]
                data['name'] = ' '.join(parts[1:]) if len(parts) > 1 else title_clean

        # Parse infobox if present
        infobox_match = re.search(r'\{\{[Ii]nfobox[^}]*\|([^}]+)\}\}', content, re.DOTALL)
        if infobox_match:
            infobox = infobox_match.group(1)

            # Extract fields from infobox
            field_patterns = {
                'engine': r'\|\s*engine\s*=\s*([^\|\n]+)',
                'horsepower': r'\|\s*(?:power|horsepower|hp)\s*=\s*(\d+)',
                'top_speed': r'\|\s*(?:top[_ ]?speed|max[_ ]?speed)\s*=\s*(\d+)',
                'year': r'\|\s*(?:year|production|model[_ ]?year)\s*=\s*(\d{4})',
            }

            for field, pattern in field_patterns.items():
                match = re.search(pattern, infobox, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if field in ['horsepower', 'top_speed', 'year']:
                        try:
                            data[field] = int(re.search(r'\d+', value).group())
                        except (ValueError, AttributeError):
                            pass
                    else:
                        # Clean wiki markup
                        value = re.sub(r'\[\[([^|\]]+\|)?([^\]]+)\]\]', r'\2', value)
                        value = re.sub(r"'''?", '', value)
                        data[field] = value[:200]

        # Try to extract acceleration (0-60 or 0-100 times)
        accel_match = re.search(r'0[-–](?:60|100)[^0-9]*(\d+\.?\d*)\s*s', content, re.IGNORECASE)
        if accel_match:
            try:
                data['acceleration'] = float(accel_match.group(1))
            except ValueError:
                pass

        # Extract first paragraph as description
        # Remove templates, references, and get plain text
        desc_content = re.sub(r'\{\{[^}]+\}\}', '', content)
        desc_content = re.sub(r'<ref[^>]*>.*?</ref>', '', desc_content, flags=re.DOTALL)
        desc_content = re.sub(r'<ref[^/]*/?>', '', desc_content)
        desc_content = re.sub(r'\[\[([^|\]]+\|)?([^\]]+)\]\]', r'\2', desc_content)
        desc_content = re.sub(r"'''?", '', desc_content)

        # Get first meaningful paragraph
        paragraphs = [p.strip() for p in desc_content.split('\n\n') if p.strip() and not p.startswith('==')]
        if paragraphs:
            data['description'] = paragraphs[0][:500]

        return data
