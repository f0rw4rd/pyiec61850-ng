#ifndef PYIEC61850_INFOREPORTHANDLER_HPP
#define PYIEC61850_INFOREPORTHANDLER_HPP

#include "eventHandler.hpp"
#include "mms_client_connection.h"
#include <string>

/**
 * InformationReportHandler - handles MMS InformationReport callbacks
 * for TASE.2 transfer set reports.
 *
 * This is a SWIG director class: Python can override trigger() to
 * receive InformationReports from the server.
 */
class InformationReportHandler: public EventHandler {
    public:
        InformationReportHandler():
            _domain_name(""),
            _variable_list_name(""),
            _mms_value(nullptr),
            _is_variable_list_name(false)
        {}

        virtual ~InformationReportHandler() {}

        virtual void setReceivedData(void *i_data_p)
        {
            // Not used for InformationReport - data is set directly
        }

        virtual void trigger() = 0;

        // Accessors for Python director subclass
        const char* getDomainName() const { return _domain_name.c_str(); }
        const char* getVariableListName() const { return _variable_list_name.c_str(); }
        MmsValue* getMmsValue() const { return _mms_value; }
        bool getIsVariableListName() const { return _is_variable_list_name; }

        // Setters used by the subscriber
        void setDomainName(const char* name) { _domain_name = name ? name : ""; }
        void setVariableListName(const char* name) { _variable_list_name = name ? name : ""; }
        void setMmsValue(MmsValue* value) { _mms_value = value; }
        void setIsVariableListName(bool is_vln) { _is_variable_list_name = is_vln; }

    protected:
        std::string _domain_name;
        std::string _variable_list_name;
        MmsValue*   _mms_value;
        bool        _is_variable_list_name;
};


/**
 * InformationReportSubscriber - installs the MMS InformationReport
 * handler on an MmsConnection and dispatches to an InformationReportHandler.
 */
class InformationReportSubscriber: public EventSubscriber {
    public:
        InformationReportSubscriber(): EventSubscriber()
        {
            m_mms_connection = nullptr;
            m_subscriber_id = "InformationReportSubscriber";
        }

        virtual ~InformationReportSubscriber() {}

        virtual bool subscribe()
        {
            if (nullptr == m_mms_connection) {
                fprintf(stderr, "InformationReportSubscriber::subscribe() failed: 'MmsConnection' is null\n");
                return false;
            }

            // Install the MMS InformationReport handler
            MmsConnection_setInformationReportHandler(
                m_mms_connection,
                InformationReportSubscriber::triggerHandler,
                NULL
            );

            return EventSubscriber::registerNewSubscriber(this, m_subscriber_id);
        }

        // Static C callback -> acquires GIL -> calls trigger()
        static void triggerHandler(void* parameter,
                                   char* domainName,
                                   char* variableListName,
                                   MmsValue* value,
                                   bool isVariableListName)
        {
            PyThreadStateLock PyThreadLock;

            // Find the registered subscriber
            EventSubscriber* l_subscriber = EventSubscriber::findSubscriber("InformationReportSubscriber");

            if (l_subscriber) {
                EventHandler* l_handler = l_subscriber->getEventHandler();
                if (l_handler) {
                    InformationReportHandler* ir_handler =
                        static_cast<InformationReportHandler*>(l_handler);

                    // Set the report data
                    ir_handler->setDomainName(domainName);
                    ir_handler->setVariableListName(variableListName);
                    ir_handler->setMmsValue(value);
                    ir_handler->setIsVariableListName(isVariableListName);

                    // Call the Python-overridable trigger
                    ir_handler->trigger();
                }
                else {
                    fprintf(stderr, "InformationReportSubscriber::triggerHandler() failed: handler undefined\n");
                }
            }
            else {
                fprintf(stderr, "InformationReportSubscriber::triggerHandler() failed: subscriber not registered\n");
            }
        }

        // Setters
        void setMmsConnection(MmsConnection conn) { m_mms_connection = conn; }
        void setSubscriberIdentifier(const char* id) { m_subscriber_id = id ? id : "InformationReportSubscriber"; }

    protected:
        MmsConnection m_mms_connection;
        std::string   m_subscriber_id;
};

#endif
