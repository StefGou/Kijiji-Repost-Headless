import bs4, requests
from kijiji_api import get_token
from kijiji_settings import KIJIJI_USERNAME, KIJIJI_PASSWORD

session = requests.session()

# Login to Kijiji
url = 'http://www.kijiji.ca/h-kitchener-waterloo/1700212'
resp = session.get(url)

url = 'https://www.kijiji.ca/t-login.html'
resp = session.get(url)

payload = {'emailOrNickname': KIJIJI_USERNAME,
            'password': KIJIJI_PASSWORD,
            'rememberMe': 'true',
            '_rememberMe': 'on',
            'ca.kijiji.xsrf.token': get_token(resp.text, 'ca.kijiji.xsrf.token'),
            'targetUrl': 'L3QtbG9naW4uaHRtbD90YXJnZXRVcmw9TDNRdGJHOW5hVzR1YUhSdGJEOTBZWEpuWlhSVmNtdzlUREpuZEZwWFVuUmlNalV3WWpJMGRGbFlTbXhaVXpoNFRucEJkMDFxUVhsWWJVMTZZbFZLU1dGVmJHdGtiVTVzVlcxa1VWSkZPV0ZVUmtWNlUyMWpPVkJSTFMxZVRITTBVMk5wVW5wbVRHRlFRVUZwTDNKSGNtVk9kejA5XnpvMnFzNmc2NWZlOWF1T1BKMmRybEE9PQ--'
            }
resp = session.post(url, data = payload)

# This is for testing purpose only. It's replacing the getCategoryMap() function.
# test_categories = {'214': 'apartments, condos > 2 bedroom', '782': 'computer accessories > monitors', '174': 'used cars & trucks'}

def getCategoryMap(session, branchCategories, isInitialRun):
    leafCategory = {}
    newBranches = {}
    if isInitialRun:
        selectCategoryPage = session.get("https://www.kijiji.ca/p-select-category.html")
        categorySoup = bs4.BeautifulSoup(selectCategoryPage.text, "html.parser")
        for categoryNode in categorySoup.select('[id^=CategoryId]'):
            categoryName = categoryNode.get_text().strip("\n").strip()
            categoryId = categoryNode['data-cat-id']
            if (categoryNode['data-cat-leaf']=='false'):
                newBranches[categoryId] = categoryName
            else:
                leafCategory[categoryId] = categoryName
    elif not isInitialRun and not branchCategories:
        print(branchCategories)
        return {}
    else:
        for [catId, name] in branchCategories.items():
            innerSelectUrl = 'https://www.kijiji.ca/p-select-category.html?categoryId='+catId
            selectCategoryPage = session.get(innerSelectUrl)
            categorySoup = bs4.BeautifulSoup(selectCategoryPage.text, 'html.parser')
            for categoryNode in categorySoup.select('[class=category-link]'):
                categoryName = name + " > " + categoryNode.get_text().strip("\n").strip()
                categoryId = categoryNode['data-cat-id']
                if (categoryNode['data-cat-leaf']=='false'):
                    newBranches[categoryId] = categoryName
                else:
                    leafCategory[categoryId] = categoryName
    return {**leafCategory, **(getCategoryMap(session, newBranches, False))}

# This is the dictionary that would need to be saved in a json file
postAdAttributes = []
"""
postAdAttributes is a list of dictionaries that should look like this:

{
"category_name": "computer accessories > monitors",
"category_id": "782",
"attributes": [
  {
    "attribute_options": [
      {
        "option_name": "18\" and under",
        "option_id": "monitorunder18inch"
      },
      {
        "option_name": "19\"-20\"",
        "option_id": "monitor19to20inch"
      },
      {
        "option_name": "21\"-24\"",
        "option_id": "monitor21to24inch"
      },
      {
        "option_name": "25\"+",
        "option_id": "monitor25inchandabove"
      }
    ],
    "attribute_id": "monitorsize_s",
    "attribute_name": "Screen Size:"
  },
  {
    "attribute_options": [
      {
        "option_name": "Owner",
        "option_id": "ownr"
      },
      {
        "option_name": "Business",
        "option_id": "delr"
      }
    ],
    "attribute_id": "forsaleby_s",
    "attribute_name": "For Sale By:"
  }
]
}
"""

for category_id, category_name in getCategoryMap(session, [], True).items():
# for category_id, category_name in test_categories.items():  # uncomment line 26 to use this
    print("Searching", category_name, "...\n")
    category_dict = {}
    category_dict['category_id'] = category_id
    category_dict['category_name'] = category_name
    category_dict['attributes'] = []

    postingUrl="https://www.kijiji.ca/p-admarkt-post-ad.html?categoryId="+category_id
    newAdPage = session.get(postingUrl)
    newAdPageSoup = bs4.BeautifulSoup(newAdPage.text, 'html.parser')
    select_and_input = newAdPageSoup.find_all(['select', 'input'], {"name": lambda x: x and x.startswith('postAdForm.attributeMap')})



    for item in select_and_input:

        item_label = newAdPageSoup.find('label', {'for': item['id']})

        attributes = {}
        attributes['attribute_id'] = item['id']

        if item.name == "select":
            attributes['attribute_name'] = item_label.text.replace('\n','').strip()
            attributes['attribute_options'] = [{"option_id": option['value'], "option_name" : option.text} for option in item.select('option') if option['value'] != ""]

        elif item.name == "input":
            attributes['attribute_name'] = item_label.text.replace('\n', '').strip()

            # if it's a text input, there's no options, the user must enter something manually
            if item['type'] == 'text':
                attributes['attribute_options'] = None

            else:
                item_name = item.parent.text.replace('\n', '')

                # if the attribute is already in the dictionary... ad the option to the options dict
                att = next((attribute for attribute in category_dict['attributes'] if attribute.get("attribute_id") == item['id']), None)
                if att:
                    att['attribute_options'].append({"option_id": item['value'], "option_name": item_name})
                    continue

                # else, create the attribute dict and the options dict
                else:
                    attributes['attribute_options'] = [{"option_id": item['value'], "option_name": item_name}]

        category_dict['attributes'].append(attributes)

    postAdAttributes.append(category_dict)

# from pprint import pprint
# pprint(postAdAttributes)

# for category_id, category in postAdAttributes.items():
#     print(category['name'], "("+ category_id +") :")
#
#     for attribute_id, attribute in category['attributes'].items():
#         print("    ", attribute['name'], "(" + attribute_id + ")")
#
#         if attribute['attribute_options']:
#             for option_id, option_name in attribute['attribute_options'].items():
#                 print("        ", option_name, "("+option_id+")")
#         else:
#             print("         Needs user input")
#
#         print()
#
#     print("\n==========================\n")

import json
with open('kijiji_api.json', 'w') as fp:
    json.dump(postAdAttributes, fp)
