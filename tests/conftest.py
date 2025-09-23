# Silence InsecureRequestWarning globally for all tests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
