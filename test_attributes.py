import bs4, requests
from KijijiApi import getToken

kijiji_username = ""
kijiji_password = ""

session = requests.session()

# Login to Kijiji
url = 'http://www.kijiji.ca/h-kitchener-waterloo/1700212'
resp = session.get(url)

url = 'https://www.kijiji.ca/t-login.html'
resp = session.get(url)

payload = {'emailOrNickname': kijiji_username,
            'password': kijiji_password,
            'rememberMe': 'true',
            '_rememberMe': 'on',
            'ca.kijiji.xsrf.token': getToken(resp.text, 'ca.kijiji.xsrf.token'),
            'targetUrl': 'L3QtbG9naW4uaHRtbD90YXJnZXRVcmw9TDNRdGJHOW5hVzR1YUhSdGJEOTBZWEpuWlhSVmNtdzlUREpuZEZwWFVuUmlNalV3WWpJMGRGbFlTbXhaVXpoNFRucEJkMDFxUVhsWWJVMTZZbFZLU1dGVmJHdGtiVTVzVlcxa1VWSkZPV0ZVUmtWNlUyMWpPVkJSTFMxZVRITTBVMk5wVW5wbVRHRlFRVUZwTDNKSGNtVk9kejA5XnpvMnFzNmc2NWZlOWF1T1BKMmRybEE9PQ--'
            }
resp = session.post(url, data = payload)

# This is for testing purpose only. It's replacing the getCategoryMap() function.
test_categories = {'214': 'apartments, condos > 2 bedroom', '782': 'computer accessories > monitors', '174': 'used cars & trucks'}

# This is the dictionary that would need to be saved in a json file
postAdAttributes = {}
"""
postAdAttributes is a dictionary that should look like this:

{
"category_id": 
    {
    "name": "category_name",
    
    "attributes": 
        {
        "attribute_id": 
            {
            "name": "attribute_name",
            "options": 
                {
                "option1_value": "option1_name",
                "option2_value": "option2_name",
                "option3_value": "option3_name"
                }
            }
        }
    }
}
"""

for category_id, category_name in test_categories.items():  # for k, v in getCategoryMap(session, [], True).items():
    print("Searching", category_name, "...\n")

    postAdAttributes[category_id] = {}
    postAdAttributes[category_id]['name'] = category_name

    postingUrl="https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId="+category_id
    newAdPage = session.get(postingUrl)
    newAdPageSoup = bs4.BeautifulSoup(newAdPage.text, 'html.parser')
    select_and_input = newAdPageSoup.find_all(['select', 'input'], {"name": lambda x: x and x.startswith('postAdForm.attributeMap')})

    postAdAttributes[category_id]['attributes'] = {}

    for item in select_and_input:

        item_label = newAdPageSoup.find('label', {'for': item['id']})

        if item.name == "select":
            postAdAttributes[category_id]['attributes'][item['id']] = {
                'name' : item_label.text.replace('\n','').strip(),
                'options' : {option['value'] : option.text for option in item.select('option') if option['value'] != ""}
            }

        elif item.name == "input":

            # if it's a text input, there's no options, the user must enter something manually
            if item['type'] == 'text':
                postAdAttributes[category_id]['attributes'][item['id']] = {
                    'name': item_label.text.replace('\n', '').strip(),
                    'options': None
                }

            else:
                item_name = item.parent.text.replace('\n', '')

                # if the attribute is already in the dictionary... ad the option to the options dict
                if item['id'] in postAdAttributes[category_id]['attributes'].keys():
                    postAdAttributes[category_id]['attributes'][item['id']]['options'][item['value']] = item_name

                # else, create the attribute dict and the options dict
                else:
                    postAdAttributes[category_id]['attributes'][item['id']] = {
                        'name': item_label.text.replace('\n', '').strip(),
                        'options': {item['value']: item_name}
                    }

# from pprint import pprint
# pprint(postAdAttributes)

for category_id, category in postAdAttributes.items():
    print(category['name'], "("+ category_id +") :")

    for attribute_id, attribute in category['attributes'].items():
        print("    ", attribute['name'], "(" + attribute_id + ")")

        if attribute['options']:
            for option_id, option_name in attribute['options'].items():
                print("        ", option_name, "("+option_id+")")
        else:
            print("         Needs user input")

        print()

    print("\n==========================\n")
