import gdata.gauth
import gdata.docs.client

def get_gdocs(gclient):
    return [(r.resource_id.text, r.title.text) for r in gclient.get_all_resources()] 

SCOPES = ['https://docs.google.com/feeds/',
          'https://spreadsheets.google.com/feeds/' ] 
USER_AGENT = "OpenPLM"

def get_gclient(valid_credential):
    docs_client = gdata.docs.client.DocsClient(source=USER_AGENT)
    cr = valid_credential
    token = gdata.gauth.OAuth2Token(
          cr.client_id, cr.client_secret, SCOPES, cr.user_agent, 
          access_token=cr.access_token, refresh_token=cr.refresh_token)
    docs_client = token.authorize(docs_client)
    return docs_client
