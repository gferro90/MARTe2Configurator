/**
 * @file CdbWrapper.h
 * @brief Header file for class CdbWrapper
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

 * @details This header file contains the declaration of the class CdbWrapper
 * with all of its public, protected and private members. It may also include
 * definitions for inline methods which need to be visible to the compiler.
 */

#ifndef CDBWRAPPER_H_
#define 		CDBWRAPPER_H_

/*---------------------------------------------------------------------------*/
/*                        Standard header includes                           */
/*---------------------------------------------------------------------------*/
#include <stdio.h>
#include <unistd.h>
/*---------------------------------------------------------------------------*/
/*                         Project header includes                           */
/*---------------------------------------------------------------------------*/

#include "ConfigurationDatabase.h"

/*---------------------------------------------------------------------------*/
/*                           Static definitions                              */
/*---------------------------------------------------------------------------*/

using namespace MARTe;

class CdbWrapper;

extern "C" {
uint32 Create();
uint32 Create2();
void Delete(uint32 obj1,
            uint32 obj2);
bool Open(uint32 obj1,
          uint32 obj2,
          const char8 *fileName);
bool ReadAndConvert(uint32 obj1,
                    uint32 obj2,
                    const char8 * const name,
                    uint32 index,
                    char8 * value);

uint32 GetVarNelements(uint32 obj1,
                       uint32 obj2,
                       const char8 * const name);

bool MoveToRoot(uint32 obj1,
                uint32 obj2);
bool MoveToAncestor(uint32 obj1,
                    uint32 obj2,
                    const uint32 generations);
bool MoveAbsolute(uint32 obj1,
                  uint32 obj2,
                  const char8 * const path);
bool MoveRelative(uint32 obj1,
                  uint32 obj2,
                  const char8 * const path);
bool MoveToChild(uint32 obj1,
                 uint32 obj2,
                 const uint32 childIdx);
void GetName(uint32 obj1,
             uint32 obj2,
             char8 *value);
void GetChildName(uint32 obj1,
                  uint32 obj2,
                  const uint32 index,
                  char8 *value);

uint32 GetNumberOfChildren(uint32 obj1,
                           uint32 obj2);

void Purge(uint32 obj1,
           uint32 obj2);
}

/*---------------------------------------------------------------------------*/
/*                           Method definitions                              */
/*---------------------------------------------------------------------------*/

class CdbWrapper: public ConfigurationDatabase {
public:
CdbWrapper();

virtual ~CdbWrapper();

virtual bool Open(const char8 *fileName);

virtual bool ReadAndConvert(const char8 *name,
                            char8 *value,
                            uint32 index);

uint32 GetVarNelements(const char8 * const name);

};
/*---------------------------------------------------------------------------*/
/*                        Inline method definitions                          */
/*---------------------------------------------------------------------------*/

#endif /* CDBWRAPPER_H_ */

