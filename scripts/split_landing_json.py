import json
import os
import shutil

locales = ['es', 'en', 'pt']
keys_to_split = {
    'hero': 'hero.json',
    'plans': 'pricing.json',
    'faq': 'faq.json',
    'industries': 'industries.json',
    'how_it_works': 'how_it_works.json',
    'smart_infra': 'smart_infra.json'
}

for loc in locales:
    src_file = f"frontend/src/messages/{loc}/landing.json"
    dest_dir = f"frontend/src/messages/{loc}/landing"
    
    if not os.path.exists(src_file):
        continue
        
    os.makedirs(dest_dir, exist_ok=True)
    
    with open(src_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    common_data = {}
    
    for key, val in data.items():
        # Due to duplication in git stash (or before), the first occurrence in the dictionary is kept by python's json.load,
        # which effectively deduplicates it!
        if key in keys_to_split:
            # Write to its own file
            with open(os.path.join(dest_dir, keys_to_split[key]), 'w', encoding='utf-8') as out:
                json.dump({key: val}, out, ensure_ascii=False, indent=2)
        else:
            common_data[key] = val
            
    # Write the rest to common.json
    with open(os.path.join(dest_dir, 'common.json'), 'w', encoding='utf-8') as out:
        json.dump(common_data, out, ensure_ascii=False, indent=2)
        
    print(f"Split {loc} successfully.")

