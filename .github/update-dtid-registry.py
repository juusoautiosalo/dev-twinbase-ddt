import os, yaml, json, requests, dtweb

def update_dtid_rebrandly(dtid: str, hostiri: str, api_key: str, info: str) -> str:
    """
    Updates one DTID in Rebrandly. Only dtid.org supported.

    Args:
      dtid: The DT identifier of the target DT. Must be URL.
    Returns:
      The hosting URL of the DT.
    """
    print("Searching for matches for DTID: " + dtid)

    REBRANDLY_URL = "https://api.rebrandly.com/v1/links"

    registry_domain = dtid.split('/')[2]
    slashtag = dtid.split('/')[3]

    # Get link id with DTID
    # Docs: https://developers.rebrandly.com/reference/getlinks
    url = REBRANDLY_URL + '?domain.fullName=' + registry_domain + '&slashtag=' + slashtag + '&limit=2'
    headers = {
        "accept": "application/json",
        "apikey": api_key
    }
    response = requests.get(url,headers=headers)
    r = response.json()

    # Check the number of matching links given in the response
    matches = len(r)
    print('Found ' + str(matches) + ' match(es)')

    # Update DTID according to the number of matches
    if matches == 0:
        print('Creating new DTID. ' + info)

        url = "https://api.rebrandly.com/v1/links"

        payload = {
            "domain": {"fullName": registry_domain},
            "destination": hostiri,
            "slashtag": slashtag,
            "title": info
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "apikey": api_key
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.text
    elif matches == 1:
        print('Updating existing DTID. ' + info)
        linkID = r[0]['id']
        
        url = "https://api.rebrandly.com/v1/links/" + linkID
        
        payload = {
            "destination": hostiri,
            "title": info
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "apikey": api_key
        }

        response = requests.post(url, json=payload, headers=headers)

        return response.text
    else:
        return "::error::Found more than one match for the DTID, could not update the entry."


curdir = os.getcwd()
repofull = os.environ["GITHUB_REPOSITORY"]

# Get api key from environment
try:
    api_key_rebrandly = os.environ["REBRANDLY_API_KEY"]
except KeyError:
    try:
        address_set_api_key = 'https://github.com/' + repofull + '/settings/secrets/actions/new'
        print("::error::Could not find REBRANDLY_API_KEY. " \
            "Please create one at https://app.rebrandly.com/account/api and set it at " + address_set_api_key + \
            " . (Requires access to the repository.)")
        exit()
    except KeyError:
        print("::error::Could not find REBRANDLY_API_KEY. " \
            "Please create one at https://app.rebrandly.com/account/api and set it to this environment.")
        exit()


# Go through twins
for folder in os.listdir(curdir):
    if os.path.isdir(folder) and folder != 'static' and folder != 'new-twin':
        print('\n')
        
        # Load YAML file
        with open(folder + '/index.yaml', 'r') as yamlfile:
            doc = yaml.load(yamlfile, Loader=yaml.FullLoader)

        # Test if DT-ID redirects to hosting IRI, modify DTID registry entry if not
        print('Testing DTID: ' + doc['dt-id'])
        current = dtweb.client.fetch_host_url(doc['dt-id'])
        print('Current result: ' + current)

        if not (current == doc['hosting-iri'] + '/'):
            print('Redirect does not match, updating DTID')
            info = 'Owner: https://github.com/' + repofull
            result = update_dtid_rebrandly(doc['dt-id'], doc['hosting-iri'], api_key_rebrandly, info)
            # print(result)
            print('Finished updating DTID: ' + doc['dt-id'])
        else:
            print('Test successful: DT-ID redirects to hosting IRI for ' + doc['name'])

print('Finished updating DTIDs.')
