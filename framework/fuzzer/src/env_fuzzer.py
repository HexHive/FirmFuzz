#Specify the root dir of the fuzzer
FUZZER_ROOT_DIR = '/home/prex94/firmfuzz-suffix/framework/fuzzer/'

#Directory where the data is held
FUZZER_DATA_DIR = FUZZER_ROOT_DIR + 'data/'

#Fuzzer operations
FUZZER_OPS_DIR = FUZZER_DATA_DIR + 'fuzzer_op/'

#Unidentifed html attributes list
FUZZER_UNIDENTIFIED = FUZZER_DATA_DIR + 'list/'

#Fuzzer Logs
FUZZER_LOGS = FUZZER_DATA_DIR + 'logs/'

#Fuzzer temporary data
FUZZER_TEMP = FUZZER_DATA_DIR + 'temp/'

#Logs all the requests made from the browser to the server
LOG_FILE= FUZZER_LOGS + 'log.json'
BACKUP_LOG = FUZZER_LOGS + 'backup_log.json'

#Logs all the pages that on retrieval returned a 4xx or 5xx error
ERROR_FILE= FUZZER_LOGS + 'error.txt'

#File which holds all the accessible URL's mapped through orthogonal means
VULN_FILE= FUZZER_OPS_DIR + 'analysis.txt'

#File responsible for switching the proxy into different modes
PROXY_MODE_FILE= FUZZER_OPS_DIR + 'proxy_mode'

#The database of our payloads for different attacks
EXPLOIT_DB= FUZZER_OPS_DIR + 'exploits'

#Holds the legitimate HTTP request trapped by the proxy
REQUEST_FILE= FUZZER_LOGS + 'request.txt'

#Holds optional credential for the target firmware if they are already known
CREDENTIAL_FILE= FUZZER_OPS_DIR + 'credentials.txt'
CREDENTIAL_CORPUS = FUZZER_OPS_DIR + 'corpus.txt'

#Mac,IP HTML Input ID lists
IP_LIST= FUZZER_DATA_DIR + 'list/ip_list'
MAC_LIST=FUZZER_DATA_DIR + 'list/mac_list'

#Identifiers left unmatched by our filters, stored here for manual sorting
TEMP_LIST=FUZZER_DATA_DIR + 'list/pending_id'

#Temp stores for http request headers of firmware being run
HEADERS=FUZZER_ROOT_DIR + 'data/temp/headers.npy'

PARAMS=FUZZER_ROOT_DIR + 'data/temp/params.npy'


#Identifies location of the script responsible for rolling back the emulation to a snapshot
ROLLBACK_SCRIPT = FUZZER_ROOT_DIR +  'src/rollback.sh'

#File where the mapped URL are mantained
MAPPED_URL =FUZZER_OPS_DIR +  'mapped.txt'

#Directory holding the POC exploits generated during fuzzing
EXPLOITS = FUZZER_ROOT_DIR + 'exploited/'

#File holding the mapping of different URL to resources it touches 
CORRELATION_FILE = FUZZER_LOGS + 'correlation.txt'

#Status Macros
CAPTURE = "1"
NOCAPTURE = "0"
NO_BUTTONS = -2
UNHANDLED_POST_REQUEST = 2
POST = 3
GET = 4
UNHANDLED = 5
REQUEST_FILE_NOT_GENERATED = 6

