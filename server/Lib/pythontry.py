import ctypes
from ctypes import cdll
lib = cdll.LoadLibrary('./Build/libCdbWrapper.so')


cdbWrapper1=lib.Create()
cdbWrapper2=lib.Create2()
s=lib.Open(cdbWrapper1, cdbWrapper2, 'CFGFIle.cfg')
lib.MoveToRoot(cdbWrapper1, cdbWrapper2)
numberOfChildren=lib.GetNumberOfChildren(cdbWrapper1, cdbWrapper2)
print(numberOfChildren)
lib.MoveAbsolute(cdbWrapper1, cdbWrapper2, '+StateMachine')
log_buffer = ctypes.create_string_buffer(1024)
lib.ReadAndConvert(cdbWrapper1, cdbWrapper2, 'Class', log_buffer)

print(log_buffer.value)


