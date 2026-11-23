import os
import re
import yaml
from pypinyin import lazy_pinyin


# =========================================================
# Configuration
# =========================================================

DATA_FILE = "data/webstack.yml"
OUTPUT_DIR = "content.en/sites"
SLUG_FILE = "data/site-slugs.yml"


# =========================================================
# Generate SEO slug
# =========================================================

def make_slug(title):

    value = str(title).strip().lower()

    # Convert Chinese to pinyin
    value = "-".join(lazy_pinyin(value))

    # Replace non-English letters and digits with -
    value = re.sub(r"[^a-z0-9]+", "-", value)

    # Collapse consecutive hyphens
    value = re.sub(r"-+", "-", value)

    # Trim leading and trailing hyphens
    value = value.strip("-")

    return value


# =========================================================
# Read multiple YAML documents
# =========================================================

def load_yaml_documents():

    with open(DATA_FILE, "r", encoding="utf-8") as f:

        documents = list(yaml.safe_load_all(f))

    all_data = []

    for document in documents:

        if not document:
            continue

        if isinstance(document, list):

            all_data.extend(document)

        elif isinstance(document, dict):

            all_data.append(document)

    return all_data


# =========================================================
# Extract all sites
# =========================================================

def flatten_links(data):

    sites = []

    for category in data:

        if not isinstance(category, dict):
            continue

        # Top-level category
        for link in category.get("links", []):

            if isinstance(link, dict):

                sites.append(link)

        # Subcategory
        for subcategory in category.get("list", []):

            if not isinstance(subcategory, dict):
                continue

            for link in subcategory.get("links", []):

                if isinstance(link, dict):

                    sites.append(link)

    return sites


# =========================================================
# Clean text
# =========================================================

def clean_text(value):

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\r", " ")
    value = value.replace("\n", " ")
    value = value.replace('"', '\\"')

    return value.strip()


# =========================================================
# Generate detail pages
#
# This script is now safe to run automatically (e.g. in CI):
# it only creates detail pages that do not exist yet and never
# overwrites an existing page, so manual edits to a detail page
# are kept. To regenerate a page, delete its .md file first and
# run the script again. Pages in content.en/sites whose slug is
# no longer in data/webstack.yml are removed as orphans.
# =========================================================

def create_markdown(site, slug):

    title = str(site.get("title", "")).strip()

    if not title:
        return False

    description = clean_text(
        site.get("description", "")
    )

    website = clean_text(
        site.get("url", "")
    )

    logo = clean_text(
        site.get("logo", "")
    )

    keywords = [
        title,
        f"{title} official website",
        f"{title} introduction",
        f"{title} what is",
    ]

    content = f'''---
title: "{clean_text(title)}"
description: "{description}"
keywords:
'''

    for keyword in keywords:

        content += f'  - "{clean_text(keyword)}"\n'

    content += f'''website: "{website}"
logo: "{logo}"
slug: "{slug}"
---

# {title}

{description}

## What Is {title}?

{title} is a website worth bookmarking and using.

If you are looking for services, tools, content, or resources related to **{title}**, you can learn more here.

## Key Features

- Learn about the services {title} offers
- Browse the content {title} offers
- Find information about how to use it
- Learn about the site's key features
- Visit the official website of {title}

## Who Is It For?

{title} is for users who need related services, tools, content, or resources.

If you are looking for a similar website, learn about {title}'s key features first, then decide whether to use it.

## What Makes It Special

{title} offers content and features related to its field.

For first-time users, we recommend visiting the official website first to learn about its services, how to use them, and the latest information.

## Visit the Official Website

If you want to learn more about {title}, visit its official website.

**[Visit the Official Website of {title}]({website})**

## Frequently Asked Questions

### What Is {title}?

{title} is a website that offers related services, tools, or content.

### Where Is the Official Website of {title}?

The official website of {title} is:

{website}

### How Do I Visit {title}?

You can click the "Visit the Official Website of {title}" button above to visit the official website.

### Is {title} Worth Bookmarking?

If you use the services {title} offers often, add it to your browser bookmarks for easy access.

'''

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    filename = os.path.join(
        OUTPUT_DIR,
        slug + ".md"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)

    print(f"Generated: {filename}")

    return True


# =========================================================
# Load the existing slug map, if any
# =========================================================

def load_slug_map():

    if not os.path.exists(SLUG_FILE):

        return {}

    with open(SLUG_FILE, "r", encoding="utf-8") as f:

        data = yaml.safe_load(f)

    return data if isinstance(data, dict) else {}


# =========================================================
# Save the slug map
# =========================================================

def save_slug_map(slug_map):

    os.makedirs(
        os.path.dirname(SLUG_FILE),
        exist_ok=True
    )

    with open(
        SLUG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        yaml.safe_dump(
            slug_map,
            f,
            allow_unicode=True,
            sort_keys=False
        )

    print(f"Slug map: {SLUG_FILE}")


# =========================================================
# Main program
# =========================================================

def main():

    print("Reading:", DATA_FILE)

    data = load_yaml_documents()

    print(
        f"YAML categories read: {len(data)}"
    )

    sites = flatten_links(data)

    print(
        f"Found sites: {len(sites)}"
    )

    # data/webstack.yml lists the same site in several categories
    # (120 links, 25 unique titles). Keep only the first entry
    # for each title, otherwise duplicates get slugs like -2, -3.
    unique_sites = []
    seen_titles = set()

    for site in sites:

        title = str(site.get("title", "")).strip()

        if title and title not in seen_titles:

            seen_titles.add(title)

            unique_sites.append(site)

    sites = unique_sites

    print(
        f"Unique sites: {len(sites)}"
    )

    # The slug map in data/site-slugs.yml is the source of truth
    # for homepage links (/sites/<slug>/). Reuse its slugs so
    # existing URLs never change; only new titles get a new slug.
    existing_slugs = load_slug_map()

    success = 0
    skipped = 0
    kept = 0

    seen_slugs = set()

    slug_map = {}

    for site in sites:

        title = str(
            site.get("title", "")
        ).strip()

        if not title:

            skipped += 1
            continue

        # -----------------------------------------
        # Slug, in priority order:
        # 1. existing data/site-slugs.yml (never change a URL)
        # 2. a slug specified in webstack.yml
        # 3. generated from the title
        # -----------------------------------------

        slug = existing_slugs.get(title)

        if slug:

            slug = str(slug).strip().lower()

        else:

            slug = site.get("slug")

            if slug:

                slug = str(slug).strip().lower()

            else:

                slug = make_slug(title)

        if not slug:

            print(
                f"Skipped: {title} — could not generate a slug"
            )

            skipped += 1
            continue

        # -----------------------------------------
        # Avoid duplicate slugs
        # -----------------------------------------

        if slug in seen_slugs:

            print(
                f"Skipped duplicate slug: {title}"
                f" → {slug}"
            )

            skipped += 1
            continue

        seen_slugs.add(slug)

        # -----------------------------------------
        # Save title -> slug
        # -----------------------------------------

        slug_map[title] = slug

        # -----------------------------------------
        # Generate detail pages, but never overwrite
        # an existing page (manual edits are kept)
        # -----------------------------------------

        existing = os.path.join(
            OUTPUT_DIR,
            slug + ".md"
        )

        if os.path.exists(existing):

            print(
                f"Kept (exists): {existing}"
            )

            kept += 1

            continue

        if create_markdown(
            site,
            slug
        ):

            success += 1

        else:

            skipped += 1

    # -----------------------------------------
    # Remove detail pages whose slug is no longer
    # in data/webstack.yml
    # -----------------------------------------

    removed = 0

    if os.path.isdir(OUTPUT_DIR):

        for filename in os.listdir(OUTPUT_DIR):

            if not filename.endswith(".md"):
                continue

            if filename[:-3] not in seen_slugs:

                orphan = os.path.join(
                    OUTPUT_DIR,
                    filename
                )

                os.remove(orphan)

                print(f"Removed orphan: {orphan}")

                removed += 1

    # -----------------------------------------
    # Save the slug map
    # -----------------------------------------

    save_slug_map(slug_map)

    print("")
    print("=" * 50)
    print("Detail pages generated")
    print("=" * 50)
    print(f"Success: {success}")
    print(f"Kept (already existed): {kept}")
    print(f"Removed orphans: {removed}")
    print(f"Skipped: {skipped}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Slug map: {SLUG_FILE}")


if __name__ == "__main__":

    main()