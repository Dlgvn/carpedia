import re
import time
import requests
from django.core.management.base import BaseCommand
from cars.models import Car, Generation


class Command(BaseCommand):
    help = 'Fetch car data from Autopedia Fandom wiki'

    BASE_URL = 'https://autopedia.fandom.com/api.php'
    HEADERS = {
        'User-Agent': 'Carpedia/1.0 (Educational car encyclopedia project)'
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of cars to fetch (0 = all)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing autopedia data before import'
        )

    def handle(self, *args, **options):
        limit = options['limit']

        if options['clear']:
            deleted = Car.objects.filter(data_source='autopedia').delete()
            self.stdout.write(f"Cleared {deleted[0]} existing autopedia cars")

        self.stdout.write("Fetching page list from Autopedia...")
        pages = self.get_all_pages(limit)
        self.stdout.write(f"Found {len(pages)} pages to process")

        created = 0
        updated = 0
        skipped = 0

        for i, page in enumerate(pages, 1):
            title = page['title']
            page_id = page['pageid']

            # Skip non-car pages
            if self.should_skip(title):
                skipped += 1
                continue

            self.stdout.write(f"[{i}/{len(pages)}] Processing: {title}")

            # Check if already exists
            existing = Car.objects.filter(wiki_page_id=page_id).first()
            if existing:
                updated += 1
                car = existing
            else:
                car = None

            # Fetch page content
            content = self.get_page_content(title)
            if not content:
                skipped += 1
                continue

            # Parse car data
            car_data = self.parse_car_data(title, content)
            if not car_data:
                skipped += 1
                continue

            # Create or update car
            if car:
                for key, value in car_data['car'].items():
                    setattr(car, key, value)
                car.save()
            else:
                car = Car.objects.create(
                    wiki_page_id=page_id,
                    data_source='autopedia',
                    **car_data['car']
                )
                created += 1

            # Create generations
            if car_data.get('generations'):
                # Clear existing generations for this car
                car.generations.all().delete()
                for gen_data in car_data['generations']:
                    Generation.objects.create(car=car, **gen_data)

            # Rate limiting
            time.sleep(0.2)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))

    def should_skip(self, title):
        """Skip non-car pages."""
        skip_patterns = [
            'Wiki', 'Category:', 'Template:', 'User:', 'File:',
            'Help:', 'Main Page', 'Portal:', 'Automotive', 'General Motors',
            'Fisker Inc', 'Fisker Automotive', 'Eagle', 'Byton', 'Genesis'
        ]
        # Skip if it's just a brand name (single word or known brand-only pages)
        single_word_brands = [
            'Acura', 'Audi', 'BMW', 'Buick', 'Cadillac', 'Chevrolet',
            'Ferrari', 'Ford', 'GMC', 'Honda', 'Hyundai', 'Jaguar',
            'Lexus', 'Mazda', 'Mercedes', 'Nissan', 'Porsche', 'Toyota', 'Volkswagen'
        ]
        title_clean = title.replace('_', ' ').strip()
        if title_clean in single_word_brands:
            return True
        return any(pattern in title for pattern in skip_patterns)

    def get_all_pages(self, limit=0):
        """Fetch all car pages from Autopedia wiki."""
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
                response = requests.get(self.BASE_URL, params=params, headers=self.HEADERS, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.stderr.write(f'Error fetching pages: {e}')
                break

            batch = data.get('query', {}).get('allpages', [])
            pages.extend(batch)

            if limit and len(pages) >= limit:
                pages = pages[:limit]
                break

            if 'continue' in data:
                apcontinue = data['continue'].get('apcontinue')
            else:
                break

        return pages

    def get_page_content(self, title):
        """Fetch wikitext content for a specific page."""
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
        """Parse car specs from Autopedia wiki content."""
        # Extract brand and name from title
        brand, name = self.extract_brand_name(title)
        if not brand or not name:
            return None

        # Extract description (first paragraph after infobox)
        description = self.extract_description(content)

        # Extract infobox data
        infobox = self.extract_infobox(content)

        car_data = {
            'car': {
                'name': name,
                'brand': brand,
                'description': description,
                'body_style': infobox.get('body_style', ''),
                'car_class': infobox.get('class', ''),
                'production_years': infobox.get('production', ''),
            },
            'generations': []
        }

        # Parse generations from content
        generations = self.parse_generations(content, infobox)
        car_data['generations'] = generations

        return car_data

    def extract_brand_name(self, title):
        """Extract brand and model name from page title."""
        # Common brand prefixes
        brands = [
            'Acura', 'Alfa Romeo', 'Aston Martin', 'Audi', 'BMW', 'Bentley',
            'Buick', 'Cadillac', 'Chevrolet', 'Chrysler', 'Dodge', 'Ferrari',
            'Fiat', 'Ford', 'GMC', 'Honda', 'Hyundai', 'Infiniti', 'Jaguar',
            'Jeep', 'Kia', 'Lamborghini', 'Land Rover', 'Lexus', 'Lincoln',
            'Lotus', 'Maserati', 'Mazda', 'McLaren', 'Mercedes-Benz', 'Mini',
            'Mitsubishi', 'Nissan', 'Pagani', 'Porsche', 'Ram', 'Rolls-Royce',
            'Subaru', 'Tesla', 'Toyota', 'Volkswagen', 'Volvo'
        ]

        title_clean = title.replace('_', ' ')

        for brand in brands:
            if title_clean.startswith(brand + ' '):
                name = title_clean[len(brand):].strip()
                return brand, name
            elif title_clean.startswith(brand):
                name = title_clean[len(brand):].strip()
                if name:
                    return brand, name

        # If no known brand, try splitting on first space
        parts = title_clean.split(' ', 1)
        if len(parts) == 2:
            return parts[0], parts[1]

        return None, None

    def extract_description(self, content):
        """Extract the first paragraph as description."""
        # Remove infobox
        content_clean = re.sub(r'\{\{[^}]+\}\}', '', content, flags=re.DOTALL)
        # Remove wiki markup
        content_clean = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', content_clean)
        content_clean = re.sub(r"'''?", '', content_clean)
        # Get first meaningful paragraph
        paragraphs = content_clean.strip().split('\n\n')
        for p in paragraphs:
            p = p.strip()
            if len(p) > 50 and not p.startswith('=='):
                return p[:500]
        return ''

    def extract_infobox(self, content):
        """Extract data from Models infobox template."""
        infobox = {}

        # Find infobox content
        infobox_match = re.search(r'\{\{(?:Models|Infobox)[^}]*\}\}', content, re.DOTALL | re.IGNORECASE)
        if not infobox_match:
            return infobox

        infobox_text = infobox_match.group(0)

        # Extract fields
        field_patterns = {
            'production': r'\|\s*production\s*=\s*([^\n|]+)',
            'model_years': r'\|\s*model[_ ]?years\s*=\s*([^\n|]+)',
            'class': r'\|\s*class\s*=\s*([^\n|]+)',
            'body_style': r'\|\s*body[_ ]?style\s*=\s*([^\n|]+)',
            'manufacturer': r'\|\s*manufacturer\s*=\s*([^\n|]+)',
        }

        for field, pattern in field_patterns.items():
            match = re.search(pattern, infobox_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean wiki markup
                value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', value)
                value = re.sub(r"'''?", '', value)
                value = re.sub(r'<[^>]+>', '', value)
                infobox[field] = value.strip()

        return infobox

    def parse_generations(self, content, infobox):
        """Parse generation-specific data from content."""
        generations = []

        # Look for generation headers like "== First Generation ==" or "=== 2001-2006 ==="
        gen_pattern = r'==+\s*([^=]+(?:Generation|gen\.|[0-9]{4}[–-][0-9]{4}|[0-9]{4}-present)[^=]*)\s*==+'
        gen_sections = re.split(gen_pattern, content, flags=re.IGNORECASE)

        if len(gen_sections) > 1:
            # Process each generation section
            for i in range(1, len(gen_sections), 2):
                if i + 1 < len(gen_sections):
                    gen_title = gen_sections[i].strip()
                    gen_content = gen_sections[i + 1]
                    gen_data = self.parse_generation_specs(gen_title, gen_content)
                    if gen_data:
                        generations.append(gen_data)
        else:
            # No explicit generations, create one from infobox
            gen_data = self.parse_generation_specs('', content)
            if gen_data:
                # Try to get years from infobox
                years = infobox.get('production', '') or infobox.get('model_years', '')
                year_match = re.search(r'(\d{4})', years)
                if year_match:
                    gen_data['year_start'] = int(year_match.group(1))
                generations.append(gen_data)

        return generations

    def parse_generation_specs(self, gen_title, content):
        """Parse specs for a specific generation."""
        gen_data = {
            'name': '',
            'code': '',
            'year_start': None,
            'year_end': None,
            'engine': '',
            'horsepower': '',
            'torque': '',
            'top_speed': '',
            'acceleration': '',
            'transmission': '',
        }

        # Parse generation title for name and years
        if gen_title:
            gen_data['name'] = gen_title

            # Extract years from title
            year_match = re.search(r'(\d{4})[–-](\d{4}|present)', gen_title, re.IGNORECASE)
            if year_match:
                gen_data['year_start'] = int(year_match.group(1))
                if year_match.group(2).lower() != 'present':
                    gen_data['year_end'] = int(year_match.group(2))

        # Extract specs from content
        spec_patterns = {
            'engine': r'(?:engine|motor)\s*[:=]\s*([^\n]+)',
            'horsepower': r'(\d+\s*hp[^,\n]*|\d+\s*kW[^,\n]*)',
            'torque': r'(\d+\s*(?:lb[·⋅]?ft|N[·⋅]?m)[^,\n]*)',
            'top_speed': r'(?:top\s*speed|max\s*speed)\s*[:=]?\s*(\d+\s*(?:mph|km/h)[^,\n]*)',
            'acceleration': r'(?:0-60|0-100|acceleration)\s*[:=]?\s*([\d.]+\s*(?:sec|s)[^,\n]*)',
            'transmission': r'(?:transmission|gearbox)\s*[:=]\s*([^\n]+)',
        }

        for field, pattern in spec_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean wiki markup
                value = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', value)
                value = re.sub(r"'''?", '', value)
                value = re.sub(r'<[^>]+>', '', value)
                gen_data[field] = value[:100]  # Limit length

        return gen_data
