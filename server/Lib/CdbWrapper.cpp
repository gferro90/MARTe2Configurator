/**
 * @file CdbWrapper.cpp
 * @brief Source file for class CdbWrapper
 * @date Jun 5, 2020
 * @author Giuseppe
 *
 * @copyright Copyright 2015 F4E | European Joint Undertaking for ITER and
 * the Development of Fusion Energy ('Fusion for Energy').
 * Licensed under the EUPL, Version 1.1 or - as soon they will be approved
 * by the European Commission - subsequent versions of the EUPL (the "Licence")
 * You may not use this work except in compliance with the Licence.
 * You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
 *
 * @warning Unless required by applicable law or agreed to in writing, 
 * software distributed under the Licence is distributed on an "AS IS"
 * basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the Licence permissions and limitations under the Licence.

 * @details This source file contains the definition of all the methods for
 * the class CdbWrapper (public, protected, and private). Be aware that some 
 * methods, such as those inline could be defined on the header file, instead.
 */

/*---------------------------------------------------------------------------*/
/*                         Standard header includes                          */
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
/*                         Project header includes                           */
/*---------------------------------------------------------------------------*/

#include "CdbWrapper.h"
#include "BasicFile.h"
#include "StreamString.h"
#include "StandardParser.h"

/*---------------------------------------------------------------------------*/
/*                           Static definitions                              */
/*---------------------------------------------------------------------------*/

extern "C" {
uint64 objP = 0ull;

uint32 Create() {
    CdbWrapper *obj = new CdbWrapper;
    objP = (uint64) obj;
    return (uint32) objP;
}

uint32 Create2() {
    return (uint32)(objP >> 32);
}
void Delete(uint32 obj1,
            uint32 obj2) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    delete obj;
}
bool Open(uint32 obj1,
          uint32 obj2,
          const char8 *fileName) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->Open(fileName);
}
bool ReadAndConvert(uint32 obj1,
                    uint32 obj2,
                    const char8 * const name,
                    uint32 index,
                    char8 *value) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->ReadAndConvert(name, value, index);
}
uint32 GetVarNelements(uint32 obj1,
                       uint32 obj2,
                       const char8 * const name) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->GetVarNelements(name);
}
bool MoveToRoot(uint32 obj1,
                uint32 obj2) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->MoveToRoot();
}
bool MoveToAncestor(uint32 obj1,
                    uint32 obj2,
                    const uint32 generations) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->MoveToAncestor(generations);
}
bool MoveAbsolute(uint32 obj1,
                  uint32 obj2,
                  const char8 * const path) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->MoveAbsolute(path);
}
bool MoveRelative(uint32 obj1,
                  uint32 obj2,
                  const char8 * const path) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->MoveRelative(path);
}
bool MoveToChild(uint32 obj1,
                 uint32 obj2,
                 const uint32 childIdx) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->MoveToChild(childIdx);
}
void GetName(uint32 obj1,
             uint32 obj2,
             char8 *value) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    const char8 *name = obj->GetName();
    uint32 strLen = StringHelper::Length(name);
    MemoryOperationsHelper::Copy(value, name, strLen);
}
void GetChildName(uint32 obj1,
                  uint32 obj2,
                  const uint32 index,
                  char8 *value) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    const char8* childName = obj->GetChildName(index);
    uint32 strLen = StringHelper::Length(childName);
    MemoryOperationsHelper::Copy(value, childName, strLen);
}

uint32 GetNumberOfChildren(uint32 obj1,
                           uint32 obj2) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->GetNumberOfChildren();
}
void Purge(uint32 obj1,
           uint32 obj2) {
    CdbWrapper *obj = (CdbWrapper *) ((uint64) obj1 + (((uint64) obj2) << 32));
    return obj->Purge();
}
}

/*---------------------------------------------------------------------------*/
/*                           Method definitions                              */
/*---------------------------------------------------------------------------*/

CdbWrapper::CdbWrapper() :
        ConfigurationDatabase() {
}

CdbWrapper::~CdbWrapper() {
    // Auto-generated destructor stub for CdbWrapper
    // TODO Verify if manual additions are needed
}

bool CdbWrapper::Open(const char8 *fileName) {
    //auto parsing
    BasicFile cfgFile;

    bool ret = cfgFile.Open(fileName, BasicFile::ACCESS_MODE_R);
    if (ret) {

        cfgFile.Seek(0ull);
        ConfigurationDatabase cdb;
        StreamString strerr;
        StandardParser parser(cfgFile, *this, &strerr);

        ret = parser.Parse();

        if (!ret) {
            printf("Failed to parse file %s\n", strerr.Buffer());
        }
        else {
            MoveToRoot();
        }
    }
    else {
        printf("Failed to open file %s\n", fileName);
    }
    return ret;
}

bool CdbWrapper::ReadAndConvert(const char8 *name,
                                char8 *value,
                                uint32 index) {

    MemoryOperationsHelper::Set(value, '\0', 1024u);
    AnyType at = this->GetType(name);
    bool ret = !at.IsVoid();
    if (ret) {
        uint32 numberOfDims = at.GetNumberOfDimensions();
        if (numberOfDims > 0u) {
            if (index < at.GetNumberOfElements(numberOfDims-1u)) {
                at = at[index];
                ret = !at.IsVoid();
            }
        }
        else {
            ret = (index == 0u);
        }
        if (ret) {
            StreamString out;
            out.Printf("%!", at);
            MemoryOperationsHelper::Copy(value, out.Buffer(), out.Size());
        }
    }
    return ret;
}

uint32 CdbWrapper::GetVarNelements(const char8 * const name) {
    AnyType at = this->GetType(name);
    uint32 ret = 0u;
    uint32 numberOfDims = at.GetNumberOfDimensions();
    if (!at.IsVoid()) {
        if (numberOfDims > 0u) {
            ret = at.GetNumberOfElements(numberOfDims-1u);
        }
        else{
            ret = at.GetNumberOfElements(0u);
        }
    }
    return ret;
}
