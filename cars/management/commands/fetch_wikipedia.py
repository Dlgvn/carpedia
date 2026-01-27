import re
import requests
from django.core.management.base import BaseCommand
from cars.models import Car


class Command(BaseCommand):
    help = 'Fetch car data from Wikipedia'

    BASE_URL = 'https://en.wikipedia.org/w/api.php'
    HEADERS = {
        'User-Agent': 'Carpedia/1.0 (Educational car encyclopedia project; contact@carpedia.local)'
    }

    # Major car manufacturer categories to fetch from
    CATEGORIES = [
        'BMW vehicles',
        'Toyota vehicles',
        'Honda vehicles',
        'Mercedes-Benz vehicles',
        'Audi vehicles',
        'Volkswagen vehicles',
        'Ford vehicles',
        'Chevrolet vehicles',
        'Porsche vehicles',
        'Ferrari vehicles',
        'Lamborghini vehicles',
        'Nissan vehicles',
        'Mazda vehicles',
        'Subaru vehicles',
        'Lexus vehicles',
        'Acura vehicles',
        'Hyundai vehicles',
        'Kia vehicles',
        'Volvo vehicles',
        'Jaguar vehicles',
        'Land Rover vehicles',
        'Jeep vehicles',
        'Dodge vehicles',
        'Chrysler vehicles',
        'Cadillac vehicles',
        'Buick vehicles',
        'Tesla vehicles',
        'Alfa Romeo vehicles',
        'Maserati vehicles',
        'Aston Martin vehicles',
        'McLaren vehicles',
        'Bentley vehicles',
        'Rolls-Royce vehicles',
        'Mini vehicles',
        'Fiat vehicles',
        'Peugeot vehicles',
        'Renault vehicles',
        'Citroën vehicles',
        'Skoda vehicles',
        'Seat vehicles',
        'Mitsubishi vehicles',
        'Suzuki vehicles',
        'Infiniti vehicles',
        'Genesis vehicles',
        'Lotus vehicles',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of pages to fetch (0 for all)',
        )
        parser.add_argument(
            '--category',
            type=str,
            default='',
            help='Fetch from specific category only (e.g., "BMW vehicles")',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        single_category = options['category']

        categories = [single_category] if single_category else self.CATEGORIES

        self.stdout.write('Fetching car pages from Wikipedia...')

        all_pages = []
        for category in categories:
            self.stdout.write(f'Fetching category: {category}')
            pages = self.fetch_category_pages(category, limit - len(all_pages) if limit else 0)
            all_pages.extend(pages)

            if limit and len(all_pages) >= limit:
                all_pages = all_pages[:limit]
                break

        # Remove duplicates by page ID
        seen_ids = set()
        unique_pages = []
        for page in all_pages:
            if page['pageid'] not in seen_ids:
                seen_ids.add(page['pageid'])
                unique_pages.append(page)

        self.stdout.write(f'Found {len(unique_pages)} unique pages to process')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for i, page in enumerate(unique_pages, 1):
            page_id = page['pageid']
            title = page['title']

            # Skip non-car pages
            if ':' in title or title.startswith('List of'):
                skipped_count += 1
                continue

            # Check if already exists in database
            existing = Car.objects.filter(wikipedia_page_id=page_id).first()

            # Fetch page content
            content = self.fetch_page_content(title)
            if not content:
                skipped_count += 1
                continue

            # Parse car data from wiki content
            car_data = self.parse_car_data(title, content)
            if not car_data.get('brand') or not car_data.get('name'):
                skipped_count += 1
                continue

            car_data['wikipedia_page_id'] = page_id
            car_data['data_source'] = 'wikipedia'

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
            if i % 25 == 0:
                self.stdout.write(f'Processed {i}/{len(unique_pages)} pages... (Created: {created_count}, Updated: {updated_count})')

        self.stdout.write(self.style.SUCCESS(
            f'Done! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'
        ))

    def fetch_category_pages(self, category, limit=0):
        """Fetch pages from a Wikipedia category."""
        pages = []
        cmcontinue = None

        while True:
            params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': f'Category:{category}',
                'cmlimit': 500,
                'cmtype': 'page',
                'format': 'json',
            }
            if cmcontinue:
                params['cmcontinue'] = cmcontinue

            try:
                response = requests.get(self.BASE_URL, params=params, headers=self.HEADERS, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.stderr.write(f'Error fetching category {category}: {e}')
                break

            batch = data.get('query', {}).get('categorymembers', [])
            pages.extend(batch)

            if limit and len(pages) >= limit:
                pages = pages[:limit]
                break

            # Check for continuation
            if 'continue' in data:
                cmcontinue = data['continue'].get('cmcontinue')
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
            response = requests.get(self.BASE_URL, params=params, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('parse', {}).get('wikitext', {}).get('*', '')
        except requests.RequestException:
            return None

    def parse_car_data(self, title, content):
        """Parse car specs from Wikipedia content with Infobox automobile."""
        data = {
            'name': '',
            'brand': '',
            'year': None,
            'description': '',
            'engine': '',
            'horsepower': None,
            'top_speed': None,
            'acceleration': None,
            'transmission': '',
            'fuel_type': '',
            'body_style': '',
            'generation_code': '',
            'generation_years': '',
        }

        # Extract infobox automobile data
        infobox_match = re.search(
            r'\{\{[Ii]nfobox\s+automobile[^}]*?\n(.*?)\n\}\}',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if infobox_match:
            infobox = infobox_match.group(1)
            data.update(self.parse_infobox(infobox))

        # Parse brand and name from title if not found in infobox
        if not data['brand'] or not data['name']:
            brand, name = self.parse_title(title)
            if not data['brand']:
                data['brand'] = brand
            if not data['name']:
                data['name'] = name

        # Extract description from content
        if not data['description']:
            data['description'] = self.extract_description(content)

        return data

    def parse_infobox(self, infobox):
        """Parse fields from the infobox content."""
        data = {}

        # Field mappings: infobox field -> model field
        field_patterns = {
            'name': r'\|\s*name\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'manufacturer': r'\|\s*manufacturer\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'production': r'\|\s*production\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'model_years': r'\|\s*model_years\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'engine': r'\|\s*engine\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'transmission': r'\|\s*transmission\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'body_style': r'\|\s*body_style\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'class': r'\|\s*class\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'wheelbase': r'\|\s*wheelbase\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'length': r'\|\s*length\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'width': r'\|\s*width\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'height': r'\|\s*height\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
            'curb_weight': r'\|\s*curb_weight\s*=\s*(.+?)(?=\n\||\n\}\}|$)',
        }

        for field, pattern in field_patterns.items():
            match = re.search(pattern, infobox, re.IGNORECASE | re.DOTALL)
            if match:
                value = self.clean_wiki_markup(match.group(1).strip())
                if value:
                    if field == 'manufacturer':
                        data['brand'] = value[:100]
                    elif field == 'name':
                        data['name'] = value[:200]
                    elif field == 'engine':
                        data['engine'] = value[:200]
                        # Try to extract horsepower
                        hp_match = re.search(r'(\d{2,4})\s*(?:hp|bhp|PS|kW)', value, re.IGNORECASE)
                        if hp_match:
                            try:
                                hp_value = int(hp_match.group(1))
                                # Convert kW to hp if needed
                                if 'kW' in value[hp_match.start():hp_match.end()+5]:
                                    hp_value = int(hp_value * 1.341)
                                if hp_value < 2000:  # Sanity check
                                    data['horsepower'] = hp_value
                            except ValueError:
                                pass
                    elif field == 'transmission':
                        data['transmission'] = value[:200]
                    elif field == 'body_style':
                        data['body_style'] = value[:100]
                    elif field == 'production':
                        data['generation_years'] = value[:50]
                        # Try to extract year
                        year_match = re.search(r'(\d{4})', value)
                        if year_match:
                            try:
                                data['year'] = int(year_match.group(1))
                            except ValueError:
                                pass
                    elif field == 'model_years':
                        if not data.get('generation_years'):
                            data['generation_years'] = value[:50]
                        if not data.get('year'):
                            year_match = re.search(r'(\d{4})', value)
                            if year_match:
                                try:
                                    data['year'] = int(year_match.group(1))
                                except ValueError:
                                    pass

        return data

    def parse_title(self, title):
        """Extract brand and model name from page title."""
        # Remove parenthetical suffixes like "(automobile)" or "(car)"
        title_clean = re.sub(r'\s*\([^)]*\)\s*$', '', title).strip()

        # Known brand patterns (common first words in car articles)
        known_brands = [
            'BMW', 'Toyota', 'Honda', 'Mercedes-Benz', 'Audi', 'Volkswagen',
            'Ford', 'Chevrolet', 'Porsche', 'Ferrari', 'Lamborghini', 'Nissan',
            'Mazda', 'Subaru', 'Lexus', 'Acura', 'Hyundai', 'Kia', 'Volvo',
            'Jaguar', 'Land Rover', 'Jeep', 'Dodge', 'Chrysler', 'Cadillac',
            'Buick', 'Tesla', 'Alfa Romeo', 'Maserati', 'Aston Martin',
            'McLaren', 'Bentley', 'Rolls-Royce', 'Mini', 'Fiat', 'Peugeot',
            'Renault', 'Citroën', 'Citroen', 'Skoda', 'Seat', 'SEAT',
            'Mitsubishi', 'Suzuki', 'Infiniti', 'Genesis', 'Lotus',
        ]

        # Try to match a known brand at the start
        for brand in known_brands:
            if title_clean.lower().startswith(brand.lower()):
                name = title_clean[len(brand):].strip()
                return brand, name if name else title_clean

        # Fallback: first word is brand, rest is name
        parts = title_clean.split(None, 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0] if parts else '', title_clean

    def clean_wiki_markup(self, text):
        """Remove wiki markup from text."""
        if not text:
            return ''

        # Remove nested templates (simple approach)
        while '{{' in text and '}}' in text:
            text = re.sub(r'\{\{[^{}]*\}\}', '', text)

        # Remove wikilinks but keep display text
        text = re.sub(r'\[\[(?:[^|\]]+\|)?([^\]]+)\]\]', r'\1', text)

        # Remove external links
        text = re.sub(r'\[https?://[^\]]+\]', '', text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove bold/italic markup
        text = re.sub(r"'{2,}", '', text)

        # Remove references
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
        text = re.sub(r'<ref[^/]*/>', '', text)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def extract_description(self, content):
        """Extract first paragraph as description."""
        # Remove infoboxes and templates at the start
        content = re.sub(r'^\s*\{\{[^}]+\}\}\s*', '', content, flags=re.DOTALL)

        # Remove all templates
        while '{{' in content:
            prev_content = content
            content = re.sub(r'\{\{[^{}]*\}\}', '', content)
            if content == prev_content:
                break

        # Remove references
        content = re.sub(r'<ref[^>]*>.*?</ref>', '', content, flags=re.DOTALL)
        content = re.sub(r'<ref[^/]*/>', '', content)

        # Clean wiki markup
        content = self.clean_wiki_markup(content)

        # Get first paragraph
        paragraphs = [p.strip() for p in content.split('\n') if p.strip() and not p.startswith('==')]
        for p in paragraphs:
            if len(p) > 50:  # Skip very short lines
                return p[:500]

        return ''
