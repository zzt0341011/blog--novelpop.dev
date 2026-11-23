import os
import re
import yaml
from pypinyin import lazy_pinyin

DATA_FILE = "data/webstack.yml"
OUTPUT_DIR = "content.en/sites"
SLUG_FILE = "data/site-slugs.yml"

def make_slug(title):
    value = "-".join(lazy_pinyin(str(title).strip().lower()))
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")

def load_yaml_documents():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data=[]
        for doc in yaml.safe_load_all(f):
            if isinstance(doc,list): data.extend(doc)
            elif isinstance(doc,dict): data.append(doc)
        return data

def flatten_links(data):
    sites=[]
    for category in data:
        if not isinstance(category,dict): continue
        for link in category.get("links",[]):
            if isinstance(link,dict): sites.append(link)
        for sub in category.get("list",[]):
            if isinstance(sub,dict):
                for link in sub.get("links",[]):
                    if isinstance(link,dict): sites.append(link)
    return sites

def clean(v):
    return str(v or "").replace('"','\\"').replace("\r"," ").replace("\n"," ").strip()

def create_markdown(site, slug=None):
    title=str(site.get("title","")).strip()
    if not title: return None
    if not slug:
        slug=str(site.get("slug","")).strip().lower() or make_slug(title)
    if not slug: return None
    description=clean(site.get("description",""))
    website=clean(site.get("url",""))
    logo=clean(site.get("logo",""))
    keywords=[title,f"{title} official website",f"{title} introduction",f"{title} what is"]
    content=f'''---
title: "{clean(title)}"
description: "{description}"
keywords:
'''
    for k in keywords: content += f'  - "{clean(k)}"\n'
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
- Visit the official website of {title}

## Who Is It For?

{title} is for users who need related services, tools, content, or resources.

## What Makes It Special

{title} offers content and features related to its field.

For first-time use, we recommend visiting the official website first to learn about its services, how to use them, and the latest information.

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

Click "Visit the Official Website of {title}" to visit the official website.

### Is {title} Worth Bookmarking?

If you use the services {title} offers often, add it to your browser bookmarks.
'''
    os.makedirs(OUTPUT_DIR,exist_ok=True)
    with open(os.path.join(OUTPUT_DIR,slug+'.md'),'w',encoding='utf-8') as f: f.write(content)
    print('Generated: '+os.path.join(OUTPUT_DIR,slug+'.md'))
    return slug

def main():
    print('Reading:',DATA_FILE)
    data=load_yaml_documents(); sites=flatten_links(data)
    print(f'Found sites: {len(sites)}')
    # webstack.yml lists the same site in several categories
    # (120 links, 25 unique titles). Keep only the first entry
    # for each title, otherwise duplicates get extra pages.
    unique=[]; seen_titles=set()
    for site in sites:
        t=str(site.get('title','')).strip()
        if t and t not in seen_titles:
            seen_titles.add(t); unique.append(site)
    sites=unique; print(f'Unique sites: {len(sites)}')
    # Reuse slugs from the existing slug map so existing URLs
    # never change; only new titles get a new slug.
    existing={}
    if os.path.exists(SLUG_FILE):
        existing=yaml.safe_load(open(SLUG_FILE,encoding='utf-8')) or {}
    seen=set(); mapping={}; success=skipped=0; kept=0
    for site in sites:
        title=str(site.get('title','')).strip()
        slug=str(existing.get(title,'')).strip().lower() or str(site.get('slug','')).strip().lower() or make_slug(title)
        if not slug or slug in seen:
            skipped+=1; continue
        seen.add(slug); mapping[title]=slug
        # Never overwrite an existing detail page (manual edits are kept).
        # Delete the .md file first to regenerate it.
        if os.path.exists(os.path.join(OUTPUT_DIR,slug+'.md')):
            print('Kept (exists): '+os.path.join(OUTPUT_DIR,slug+'.md')); kept+=1; continue
        if create_markdown(site, slug): success+=1
        else: skipped+=1
    # Remove orphan detail pages no longer in data/webstack.yml.
    removed=0
    if os.path.isdir(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.md') and filename[:-3] not in seen:
                os.remove(os.path.join(OUTPUT_DIR,filename)); print('Removed orphan: '+os.path.join(OUTPUT_DIR,filename)); removed+=1
    os.makedirs('data',exist_ok=True)
    with open(SLUG_FILE,'w',encoding='utf-8') as f:
        yaml.safe_dump(mapping,f,allow_unicode=True,sort_keys=False)
    print('='*50); print('Detail pages generated'); print('='*50)
    print(f"Success: {success}"); print(f"Kept (already existed): {kept}"); print(f"Removed orphans: {removed}"); print(f"Skipped: {skipped}"); print(f'Slug map: {SLUG_FILE}')

if __name__=='__main__': main()
