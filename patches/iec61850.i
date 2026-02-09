/* File : iec61850.i */
%module(directors="1") pyiec61850
%ignore ControlObjectClient_setTestMode(ControlObjectClient self);
%ignore CDA_OperBoolean(ModelNode* parent, bool isTImeActivated);
%ignore LogicalNode_hasBufferedReports(LogicalNode* node);
%ignore LogicalNode_hasUnbufferedReports(LogicalNode* node);
%ignore MmsConnection_setIsoConnectionParameters(MmsConnection self, IsoConnectionParameters* params);
%include "stdint.i"
%{
#include <iec61850_client.h>
#include <iec61850_model.h>
#include <iec61850_server.h>
ModelNode* toModelNode(LogicalNode * ln)
{
    return (ModelNode*) ln;
}
ModelNode* toModelNode(DataObject * DO)
{
    return (ModelNode*) DO;
}
char* toCharP(void * v)
{
    return (char *) v;
}
DataAttribute* toDataAttribute(DataObject * DO)
{ return (DataAttribute*)DO;}
DataAttribute* toDataAttribute(ModelNode * MN)
{ return (DataAttribute*)MN;}
DataObject* toDataObject(ModelNode * MN)
{ return (DataObject*)MN;}
%}
// Custom typemap for IedClientError* that properly returns (result, error) tuples
%typemap(in, numinputs=0) IedClientError* error (IedClientError temp) {
    temp = IED_ERROR_OK;
    $1 = &temp;
}

%typemap(argout) IedClientError* error {
    // Create a tuple (original_result, error_code)
    PyObject *error_obj = PyLong_FromLong((long)*$1);
    PyObject *old_result = $result;
    
    $result = PyTuple_New(2);
    PyTuple_SetItem($result, 0, old_result);
    PyTuple_SetItem($result, 1, error_obj);
}

%include "cstring.i"
%cstring_bounded_output(char *buffer, 1024);

/* ================================================================
 * NULL-safety typemaps - systematic protection against segfaults
 * These must appear BEFORE the %include directives for the headers
 * they protect so that SWIG applies them during wrapper generation.
 * ================================================================ */

/* --- 1. Opaque pointer NULL checks ---
 * Raise ValueError when any function receives a NULL opaque handle.
 * These types are all typedef'd as pointers (e.g. typedef struct sX* X)
 * so the typemap target matches the typedef name directly. */

%typemap(check) IedConnection {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "IedConnection is NULL");
    }
}

%typemap(check) MmsConnection {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "MmsConnection is NULL");
    }
}

%typemap(check) GooseSubscriber {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "GooseSubscriber is NULL");
    }
}

%typemap(check) GooseReceiver {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "GooseReceiver is NULL");
    }
}

%typemap(check) GoosePublisher {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "GoosePublisher is NULL");
    }
}

%typemap(check) LinkedList {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "LinkedList is NULL");
    }
}

%typemap(check) ControlObjectClient {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "ControlObjectClient is NULL");
    }
}

%typemap(check) ClientReportControlBlock {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "ClientReportControlBlock is NULL");
    }
}

%typemap(check) ClientDataSet {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "ClientDataSet is NULL");
    }
}

%typemap(check) ClientGooseControlBlock {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "ClientGooseControlBlock is NULL");
    }
}

%typemap(check) MmsValue* {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "MmsValue is NULL");
    }
}

%typemap(check) const MmsValue* {
    if (!$1) {
        SWIG_exception_fail(SWIG_ValueError, "MmsValue is NULL");
    }
}

/* --- 2. String parameter NULL/empty checks ---
 * Identifiers, paths, hostnames etc. that must not be NULL or empty. */

%typemap(check) const char* hostname {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "hostname must not be empty or NULL");
    }
}

%typemap(check) const char* serverName {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "serverName must not be empty or NULL");
    }
}

%typemap(check) const char* objectReference {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "objectReference must not be empty or NULL");
    }
}

%typemap(check) const char* dataAttributeReference {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "dataAttributeReference must not be empty or NULL");
    }
}

%typemap(check) const char* dataSetReference {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "dataSetReference must not be empty or NULL");
    }
}

%typemap(check) const char* rcbReference {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "rcbReference must not be empty or NULL");
    }
}

%typemap(check) const char* interfaceId {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "interfaceId must not be empty or NULL");
    }
}

%typemap(check) const char* fileName {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "fileName must not be empty or NULL");
    }
}

%typemap(check) const char* directoryName {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "directoryName must not be empty or NULL");
    }
}

%typemap(check) char* goCbRef {
    if (!$1 || strlen($1) == 0) {
        SWIG_exception_fail(SWIG_ValueError, "goCBRef must not be empty or NULL");
    }
}

/* --- 3. Safe _destroy functions ---
 * Make destroy/delete calls no-op on NULL instead of segfaulting. */

%exception IedConnection_destroy {
    if (arg1) { $action }
}

%exception MmsConnection_destroy {
    if (arg1) { $action }
}

%exception GooseSubscriber_destroy {
    if (arg1) { $action }
}

%exception GooseReceiver_destroy {
    if (arg1) { $action }
}

%exception GoosePublisher_destroy {
    if (arg1) { $action }
}

%exception LinkedList_destroy {
    if (arg1) { $action }
}

%exception LinkedList_destroyDeep {
    if (arg1) { $action }
}

%exception LinkedList_destroyStatic {
    if (arg1) { $action }
}

%exception ControlObjectClient_destroy {
    if (arg1) { $action }
}

%exception ClientReportControlBlock_destroy {
    if (arg1) { $action }
}

%exception ClientDataSet_destroy {
    if (arg1) { $action }
}

%exception MmsValue_delete {
    if (arg1) { $action }
}

%exception ClientGooseControlBlock_destroy {
    if (arg1) { $action }
}

/* --- 4. _create function return-NULL checks ---
 * Raise RuntimeError if allocation/creation fails and returns NULL. */

%exception IedConnection_create {
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "IedConnection_create returned NULL");
        SWIG_fail;
    }
}

%exception MmsConnection_create {
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "MmsConnection_create returned NULL");
        SWIG_fail;
    }
}

%exception GooseReceiver_create {
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "GooseReceiver_create returned NULL");
        SWIG_fail;
    }
}

%exception LinkedList_create {
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "LinkedList_create returned NULL");
        SWIG_fail;
    }
}

%exception ControlObjectClient_create {
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "ControlObjectClient_create returned NULL");
        SWIG_fail;
    }
}

%exception ClientReportControlBlock_create {
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "ClientReportControlBlock_create returned NULL");
        SWIG_fail;
    }
}

%exception ClientGooseControlBlock_create {
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError, "ClientGooseControlBlock_create returned NULL");
        SWIG_fail;
    }
}

/* ================================================================
 * End of NULL-safety typemaps
 * ================================================================ */

%include "libiec61850_common_api.h"
%include "iec61850_client.h"
%include "iso_connection_parameters.h"
%include "mms_client_connection.h"
%include "iso_connection_parameters.h"
%include "iec61850_common.h"
%include "mms_value.h"
%include "mms_common.h"
%include "iec61850_model.h"
%include "iec61850_server.h"
%include "iec61850_dynamic_model.h"
%include "iec61850_cdc.h"
%include "linked_list.h"
%include "iec61850_config_file_parser.h"

/* User-defined data types, also used: */
typedef uint64_t msSinceEpoch;
typedef uint64_t nsSinceEpoch;

ModelNode* toModelNode(LogicalNode *);
ModelNode* toModelNode(DataObject *);
DataAttribute* toDataAttribute(DataObject *);
DataAttribute* toDataAttribute(ModelNode *);
DataObject* toDataObject(ModelNode *);
char* toCharP(void *);

/* Goose Subscriber section */
%{
struct sGooseSubscriber;
typedef struct sGooseSubscriber* GooseSubscriber;
#include "goose_subscriber.h"
#include "goose_receiver.h"

void GooseSubscriber_setDstMac(GooseSubscriber subscriber,
                               uint8_t dst_mac_0,
                               uint8_t dst_mac_1,
                               uint8_t dst_mac_2,
                               uint8_t dst_mac_3,
                               uint8_t dst_mac_4,
                               uint8_t dst_mac_5)
{
    uint8_t dst_mac[6];
    dst_mac[0] = dst_mac_0;
    dst_mac[1] = dst_mac_1;
    dst_mac[2] = dst_mac_2;
    dst_mac[3] = dst_mac_3;
    dst_mac[4] = dst_mac_4;
    dst_mac[5] = dst_mac_5;

    GooseSubscriber_setDstMac(subscriber, dst_mac);
}
%}

/* Safety checks for GOOSE APIs to prevent segfaults from invalid args */
%exception GooseSubscriber_create {
    if (!arg1 || strlen(arg1) == 0) {
        PyErr_SetString(PyExc_ValueError,
            "goCBRef must not be empty or NULL");
        SWIG_fail;
    }
    $action
    if (!result) {
        PyErr_SetString(PyExc_RuntimeError,
            "GooseSubscriber_create returned NULL");
        SWIG_fail;
    }
}

%exception GooseReceiver_start {
    if (arg1 && GooseReceiver_isRunning(arg1)) {
        PyErr_SetString(PyExc_RuntimeError,
            "GooseReceiver is already running");
        SWIG_fail;
    }
    $action
}

%exception GooseReceiver_startThreadless {
    if (arg1 && GooseReceiver_isRunning(arg1)) {
        PyErr_SetString(PyExc_RuntimeError,
            "GooseReceiver is already running");
        SWIG_fail;
    }
    $action
}

%include "goose_subscriber.h"
%include "goose_receiver.h"

/* Clear GOOSE-specific exception handlers so they don't affect later functions */
%exception GooseSubscriber_create;
%exception GooseReceiver_start;
%exception GooseReceiver_startThreadless;

void GooseSubscriber_setDstMac(GooseSubscriber subscriber,
                               uint8_t dst_mac_0,
                               uint8_t dst_mac_1,
                               uint8_t dst_mac_2,
                               uint8_t dst_mac_3,
                               uint8_t dst_mac_4,
                               uint8_t dst_mac_5);

/* Event Handler section */
%feature("director") RCBHandler;
%feature("director") GooseHandler;
%feature("director") CommandTermHandler;
%feature("director") CheckHandlerForPython;
%feature("director") WaitForExecutionHandlerForPython;
%feature("director") ControlHandlerForPython;
%feature("director") InformationReportHandler;
%{
#include "eventHandlers/eventHandler.hpp"
#include "eventHandlers/reportControlBlockHandler.hpp"
#include "eventHandlers/gooseHandler.hpp"
#include "eventHandlers/commandTermHandler.hpp"
#include "eventHandlers/controlActionHandler.hpp"
#include "eventHandlers/informationReportHandler.hpp"
std::map< std::string, EventSubscriber*> EventSubscriber::m_subscriber_map = {};
%}

%include "eventHandlers/eventHandler.hpp"
%include "eventHandlers/reportControlBlockHandler.hpp"
%include "eventHandlers/gooseHandler.hpp"
%include "eventHandlers/commandTermHandler.hpp"
%include "eventHandlers/controlActionHandler.hpp"
%include "eventHandlers/informationReportHandler.hpp"

/* Goose Publisher section */
%{
#include "goose_publisher.h"

void LinkedList_destroyDeep_MmsValueDelete(LinkedList dataSetValues)
{
    LinkedList_destroyDeep(dataSetValues, (LinkedListValueDeleteFunction) MmsValue_delete);
}
void CommParameters_setDstAddress(CommParameters *gooseCommParameters,
                                  uint8_t dst_mac_0,
                                  uint8_t dst_mac_1,
                                  uint8_t dst_mac_2,
                                  uint8_t dst_mac_3,
                                  uint8_t dst_mac_4,
                                  uint8_t dst_mac_5)
{
    gooseCommParameters->dstAddress[0] = dst_mac_0;
    gooseCommParameters->dstAddress[1] = dst_mac_1;
    gooseCommParameters->dstAddress[2] = dst_mac_2;
    gooseCommParameters->dstAddress[3] = dst_mac_3;
    gooseCommParameters->dstAddress[4] = dst_mac_4;
    gooseCommParameters->dstAddress[5] = dst_mac_5;
}
%}
%include "goose_publisher.h"
void LinkedList_destroyDeep_MmsValueDelete(LinkedList dataSetValues);
void CommParameters_setDstAddress(CommParameters *gooseCommParameters,
                                  uint8_t dst_mac_0,
                                  uint8_t dst_mac_1,
                                  uint8_t dst_mac_2,
                                  uint8_t dst_mac_3,
                                  uint8_t dst_mac_4,
                                  uint8_t dst_mac_5);


/* Wrapper for synchronous functions */
%{
#include "servicePythonWrapper.hpp"
%}
%include "servicePythonWrapper.hpp"
