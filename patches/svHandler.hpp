#ifndef PYIEC61850_SVHANDLER_HPP
#define PYIEC61850_SVHANDLER_HPP

#include "eventHandler.hpp"
#include "sv_subscriber.h"
#include <cstdio>

/**
 * SVHandler - handles IEC 61850 Sampled Values callbacks.
 *
 * libiec61850's SV subscribe API is callback-based: SVSubscriber_setListener
 * registers an SVUpdateListener that is invoked (from the SVReceiver thread)
 * for each received ASDU. Python cannot supply a C function pointer, so this
 * SWIG director lets Python override trigger() and read the ASDU that was
 * stashed just before the call. The SVSubscriber_ASDU is only valid inside the
 * callback (it is statically allocated per libiec61850's contract), so the
 * Python trigger() must copy out any values it wants during the call.
 */
class SVHandler: public EventHandler {
    public:
        SVHandler(): _libiec61850_sv_asdu(nullptr) {}
        virtual ~SVHandler() {}

        virtual void setReceivedData(void *i_data_p)
        {
            SVSubscriber_ASDU *l_my_data_p = static_cast<SVSubscriber_ASDU*>(i_data_p);
            _libiec61850_sv_asdu = *l_my_data_p;
        }

        virtual void trigger() = 0;

        // The ASDU received in the current callback. Only valid during trigger().
        SVSubscriber_ASDU _libiec61850_sv_asdu;
};


/**
 * SVSubscriberForPython - installs the SVUpdateListener on an SVSubscriber and
 * dispatches each ASDU to an SVHandler director.
 */
class SVSubscriberForPython: public EventSubscriber {
    public:
        SVSubscriberForPython(): EventSubscriber()
        {
            m_libiec61850_sv_subscriber = nullptr;
            m_subscriber_id = "";
        }

        virtual ~SVSubscriberForPython() {}

        virtual bool subscribe()
        {
            if (nullptr == m_libiec61850_sv_subscriber) {
                fprintf(stderr, "SVSubscriberForPython::subscribe() failed: 'SV subscriber' is null\n");
                return false;
            }

            // Install the libiec61850 SV listener. Pass 'this' as the callback
            // parameter so the static trampoline can find us directly -- an SV
            // subscriber has no goCbRef-style stable id to key a registry on.
            SVSubscriber_setListener(m_libiec61850_sv_subscriber,
                                     SVSubscriberForPython::triggerSVHandler,
                                     this);

            // Register with a per-instance id (for lifecycle bookkeeping only;
            // the callback routes via the 'this' parameter, not the registry).
            char idbuf[48];
            snprintf(idbuf, sizeof(idbuf), "SVSubscriberForPython_%p", (void*)this);
            m_subscriber_id = idbuf;

            return EventSubscriber::registerNewSubscriber(this, m_subscriber_id);
        }

        // Static method: the SVUpdateListener callback for libiec61850 in C.
        static void triggerSVHandler(SVSubscriber subscriber, void *parameter, SVSubscriber_ASDU asdu)
        {
            (void)subscriber;
            PyThreadStateLock PyThreadLock;

            SVSubscriberForPython *self = static_cast<SVSubscriberForPython*>(parameter);
            if (nullptr == self) {
                fprintf(stderr, "SVSubscriberForPython::triggerSVHandler() failed: parameter is null\n");
                return;
            }

            EventHandler *l_event_handler_p = self->getEventHandler();
            if (l_event_handler_p) {
                l_event_handler_p->setReceivedData(&asdu);
                l_event_handler_p->trigger();
            }
            else {
                fprintf(stderr, "SVSubscriberForPython::triggerSVHandler() failed: EventHandler is undefined\n");
            }
        }

        void setLibiec61850SVSubscriber(const SVSubscriber &i_libiec61850_sv_subscriber)
        {
            m_libiec61850_sv_subscriber = i_libiec61850_sv_subscriber;
        }

    protected:
        SVSubscriber m_libiec61850_sv_subscriber;
        std::string  m_subscriber_id;
};

#endif
