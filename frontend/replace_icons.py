import re

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # We will find all instances of the step icon container and replace the inner content
    # The pattern matches the container and everything inside it up to </div>
    pattern = r'(<div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">)\s*<svg[^>]*>.*?</svg>\s*(</div>)'
    
    # Wait, in bus step 3, it's a span: <span className="text-green-500 font-bold text-xl">$</span>
    pattern = r'(<div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">)\s*(?:<svg[^>]*>.*?</svg>|<span[^>]*>.*?</span>)\s*(</div>)'
    
    matches = list(re.finditer(pattern, content, flags=re.DOTALL))
    
    if len(matches) != len(replacements):
        print(f"Error: {filepath} has {len(matches)} steps but {len(replacements)} replacements provided")
        return
        
    for i, match in enumerate(matches):
        replacement_html = f'<Image src="/icons/{replacements[i]}" width={{24}} height={{24}} alt="icon" />'
        full_replacement = f'{match.group(1)}\n                {replacement_html}\n              {match.group(2)}'
        content = content.replace(match.group(0), full_replacement)
        
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Updated {filepath}")

# Train: ticket, door-enter, train, door-exit
replace_in_file('src/app/transportation/train/page.jsx', ['ticket.svg', 'door-enter.svg', 'train.svg', 'door-exit.svg'])

# Bus: hand-finger (check bus), ticket, brand-cashapp (watch fare), hand-finger (press button), door-exit (pay and get off)
# Actually, door-enter is boarding the bus from rear. Step 1 is "Check the bus", maybe hand-finger? Step 2 is Board & take a ticket (door-enter). Step 3 watch fare (brand-cashapp). Step 4 press button (hand-finger). Step 5 pay & get off (door-exit).
replace_in_file('src/app/transportation/bus/page.jsx', ['hand-finger.svg', 'door-enter.svg', 'brand-cashapp.svg', 'hand-finger.svg', 'door-exit.svg'])

# Car: license, circle-key, steering-wheel, gas-station, car
replace_in_file('src/app/transportation/car/page.jsx', ['license.svg', 'circle-key.svg', 'steering-wheel.svg', 'gas-station.svg', 'car.svg'])

