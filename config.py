
####################################################################################################
##                                          Modules                                               ##
####################################################################################################

## NLU
import dum_NLU
NLU = dum_NLU.NLU

## DM
import dum_DM
DM = dum_DM.DM

##
import dum_NLG
NLG = dum_NLG.NLG

####################################################################################################
##                                        Broker config                                           ##
####################################################################################################
ADDRESS = "iot.eclipse.org"
PORT = 1883

# Connection timeout, in secondes
CONNECTION_TIMEOUT = 30


####################################################################################################
##                                           Messages                                             ##
####################################################################################################
## Main topic
MSG_MAIN_TOPIC = "UoGSR/ca/"

## Client publishes on
MSG_CLIENT = MSG_MAIN_TOPIC+"Client/"

## For NLU, Server publishes on
MSG_SERVER_IN= MSG_MAIN_TOPIC+"Server_in/"

## For DM, NLU publishes on
MSG_NLU = MSG_MAIN_TOPIC+"NLU/"

## For NLG, DM published on
MSG_DM = MSG_MAIN_TOPIC+"DM/"

## For main server, NLG publishes on
MSG_NLG = MSG_MAIN_TOPIC+"NLG/"

## For client, main server publishes on
MSG_SERVER_OUT = MSG_MAIN_TOPIC+"Server_out/"

# Connection message from client:
MSG_CONNECTION = "new client connected"

