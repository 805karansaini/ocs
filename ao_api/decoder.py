import inspect
import logging

from ao_api.message import IN
from ao_api.wrapper import *  # @UnusedWildImport TODO remove

logger = logging.getLogger(__name__)


class HandleInfo:
    def __init__(self, wrap=None, proc=None):
        self.wrapperMeth = wrap
        self.wrapperParams = None
        self.processMeth = proc
        if wrap is None and proc is None:
            raise ValueError("both wrap and proc can't be None")

    def __str__(self):
        s = "wrap:%s meth:%s prms:%s" % (
            self.wrapperMeth,
            self.processMeth,
            self.wrapperParams,
        )
        return s


class Decoder:
    def __init__(self, wrapper):
        self.wrapper: EWrapper = wrapper
        self.discoverParams()

    def discoverParams(self):
        meth2handleInfo = {}
        for handleInfo in self.msgId2handleInfo.values():
            meth2handleInfo[handleInfo.wrapperMeth] = handleInfo

        methods = inspect.getmembers(EWrapper, inspect.isfunction)
        for _, meth in methods:
            # logger.debug("meth %s", name)
            sig = inspect.signature(meth)
            handleInfo = meth2handleInfo.get(meth, None)
            if handleInfo is not None:
                handleInfo.wrapperParams = sig.parameters

    def interpret(self, response_mssg):

        # Get response type
        response_type = response_mssg["response_type"]

        handleInfo = self.msgId2handleInfo.get(response_type, None)

        if handleInfo is None:
            print("handle is none")
            logger.debug("%s: no handleInfo", response_mssg)
            return

        try:
            # Call Wrapper Method here
            if handleInfo.wrapperMeth is not None:
                pass

                # TODO no method currently routed to the Ewrapper
                # logger.debug("In interpret(), handleInfo: %s", handleInfo)
                # self.interpretWithSignature(response_mssg, handleInfo)

            # Call ProcessMethod/Decoder Method
            elif handleInfo.processMeth is not None:
                handleInfo.processMeth(self, response_mssg)

        except Exception as e:
            pass
            # TODO - Check
            # theBadMsg = ",".join(response_mssg)
            # self.wrapper.error(
            #     NO_VALID_ID, BAD_MESSAGE.code(), BAD_MESSAGE.msg() + theBadMsg
            # )
            # raise

    def process_error_msg(self, response_mssg):

        reqId = response_mssg["request_id"]
        error_dict = response_mssg["result"][0]

        # errorCode = error_dict.get('error_code', None)
        # errorString = error_dict.get('error_msg', None)
        # advancedOrderRejectJson = error_dict.get('advance_order_reject_json', None)
        errorCode = None
        errorString = error_dict
        advancedOrderRejectJson = None

        self.wrapper.error(reqId, errorCode, errorString, advancedOrderRejectJson)

    def process_historical_data_msg(self, response_mssg):
        reqId = response_mssg["request_id"]
        itemCount = response_mssg["result"]

        for data_dict in itemCount:
            bar = {}
            bar["datetime"] = data_dict["datetime"]
            bar["open"] = data_dict["open"]
            bar["high"] = data_dict["high"]
            bar["low"] = data_dict["low"]
            bar["close"] = data_dict["close"]
            bar["volume"] = data_dict["volume"]

            self.wrapper.historical_data(reqId, bar)

    def process_historical_data_end_msg(self, response_mssg):
        # {'request_id': '12345', 'response_type': 'data_end', 'result': ['Historical Data End.']}
        # {'request_id': '12346', 'response_type': 'error', 'result': ['149928']}

        try:
            reqId = response_mssg["request_id"]
            start = None  # response_mssg["result"][0]
            end = None
            self.wrapper.historical_data_end(
                reqId,
            )
        except Exception as e:
            print(
                e,
            )

    msgId2handleInfo = {
        IN.ERR_MSG: HandleInfo(proc=process_error_msg),
        IN.HISTORICAL_DATA: HandleInfo(proc=process_historical_data_msg),
        IN.HISTORICAL_DATA_END: HandleInfo(proc=process_historical_data_end_msg),
    }
