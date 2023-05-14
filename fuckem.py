import requests
import time
import os
import json
from pathlib import Path
DB_PATH = Path('db.json')
EVENTER_DOMAIN = "https://www.eventer.co.il"
TARGET_SELLER = "KULIALMA"


class CouldNotFetchEventError(Exception):
    pass


class CouldNotGetTicketsError(Exception):
    pass


class CouldNotGetUserData(Exception):
    pass


def get_event_info_urls():
    headers = {'Accept': 'application/json'}
    r = requests.get(
        "{domain}/user/{user}/getData".format(domain=EVENTER_DOMAIN, user=TARGET_SELLER), headers=headers)
    if not r.ok:
        raise CouldNotGetUserData()
    events = r.json()["events"]
    event_links = ["{domain}/events/explainNames/{link_name}.js".format(
        domain=EVENTER_DOMAIN, link_name=event["linkName"]) for event in events]
    print("Event links: {}".format(event_links))
    return event_links


def get_event_info():
    headers = {'Accept': 'application/json'}
    for event in get_event_info_urls():
        print("Fetching {}".format(event))
        r = requests.get(event, headers=headers)
        if not r.ok:
            print("Could not fetch {event}".format(event=event))
            continue
        yield r.json()


def get_ticket_types(event_id):
    uri = "{domain}/events/{event_id}/ticketTypes.js".format(
        domain=EVENTER_DOMAIN, event_id=event_id)
    headers = {'Accept': 'application/json'}
    r = requests.get(uri, headers=headers)
    if not r.ok:
        raise CouldNotGetTicketsError()
    return r.json()


def generate_purchase(name, id, phone, email, date, age, tickets, event_info):
    return {
        "sales": [
            {
                "guests": [
                    {
                        "isBuyer": True,
                        "isPassportAsId": False,
                        "ticketType": tickets['ticketTypes'][0]['_id'],
                        "ticketsForQuestions": {
                            tickets['ticketTypes'][0]['_id']: tickets['ticketTypes'][0]['_id']
                        },
                        "name": name,
                        "id": id,
                        "isOpen": False,
                        "phone": phone,
                        "emailSuggestion": None,
                        "isMale": "true",
                        "email": email,
                        "pickerOpen": False,
                        "dateOfBirth": date,
                        "saleRound": None,
                        "guestAnswers": [
                            {
                                "question": event_info['dataForSale']['settings']['guestQuestions'][1]['_id'],
                                "answers": "The will of the people"
                            }
                        ],
                        "age": age
                    }
                ],
                "shippingInfo": None,
                "shippingMethod": "homePrint",
                "lang": "he_IL",
                "discount": 0,
                "markAcceptSMSTicket": False,
                "isAllowPromotionalContent": False,
                "chosenUpsaleItems": [],
                "settings": {
                    "eventType": 1,
                    "purchaseConfirm": {
                        "confirmEachPurchase": True,
                        "confirmMethod": "Questions"
                    },
                    "ageLimit": 24,
                    "allowMultipleTickets": 1,
                    "multipleCreditCards": False,
                    "namePerTicket": True,
                    "guestInfoFields": {
                        "name": {
                            "isToShow": True,
                            "isRequired": True,
                            "showInNamePerTicket": True
                        },
                        "sid": {
                            "isSupportInternationalID": True,
                            "isToShow": True,
                            "isRequired": True,
                            "showInNamePerTicket": True
                        },
                        "phone": {
                            "isSupportInternationalPhone": True,
                            "isToShow": True,
                            "isRequired": True,
                            "showInNamePerTicket": True
                        },
                        "email": {
                            "isToShow": True,
                            "isRequired": True,
                            "showInNamePerTicket": True
                        },
                        "age": {
                            "isAgeByDate": True,
                            "isToShow": True,
                            "isRequired": True,
                            "ageLimit": 24,
                            "showInNamePerTicket": True
                        },
                        "gender": {
                            "isToShow": True,
                            "isRequired": True,
                            "showInNamePerTicket": True
                        }
                    },
                    "eventCategories": event_info["event"]["eventCategories"],
                    "extraQuestions": [],
                    "extraQuestionsTranslations": [],
                    "upsaleItems": [],
                    "guestQuestions": event_info["dataForSale"]["settings"]["guestQuestions"],
                    "nonMandatoryExtraQuestions": [],
                    "showExtraQuestionsToBuyerOnly": True,
                    "askForGender": True,
                    "isTicketSectionTop": False,
                    "isSMSOptional": False,
                    "ticketDelivery": {
                        "homePrint": True
                    },
                    "isSupportMultiLanguage": True,
                    "promotionalApproval": {
                        "isRequestingApproval": False
                    },
                    "hideStartTime": False,
                    "hideEndTime": True,
                    "hideOpenDoors": False,
                    "usePrivateTerminal": False,
                    "supportedLanguages": {
                        "he_IL": True,
                        "en_EN": True,
                        "ru_RU": True,
                        "fr_FR": True
                    },
                    "defaultLanguage": "he_IL",
                    "isUseCancellationDeadline": False,
                    "isSendSMSForPendingSales": False,
                    "useAltDefaultTerminal": False,
                    "isLiveStreamEvent": False,
                    "status": 1,
                    "isSendSMSForCancelledSales": False,
                    "shippingMethod": {
                        "value": "homePrint"
                    },
                    "hasGiftCard": False
                },
                "isSendSMS": False,
                "referrer": "",
                "device": {
                    "formFactor": "Desktop",
                    "name": "Chrome"
                },
                "history": [
                ],
                "queryData": [],
                "event": event_info['event']['_id']
            }
        ],
        "paymentMethod": "credit",
        "event": event_info["event"]["_id"]
    }


def get_eventer_tag():
    resp = requests.get(
        "{}/user/KULIALMA".format(EVENTER_DOMAIN))
    start = resp.content.find(b'version="') + len(b'version="')
    end = resp.content.find(b'"', start)
    return resp.content[start:end]


def do_register(name, id, phone, email, date, age, event_info, tickets):
    purchase_req = generate_purchase(
        name, id, phone, email, date, age, tickets, event_info)

    header = {"Content-Type": "application/json;charset=UTF-8",
              "X-Eventer-Tag": get_eventer_tag()}

    print("Purchasing!")
    return requests.post(
        "{}/sales/sellFromEventLandingPage".format(EVENTER_DOMAIN), json=purchase_req, headers=header)


def load_db():
    db = []
    try:
        db = json.loads(DB_PATH.read_text())
    except:
        pass
    return db


def write_db(data):
    DB_PATH.write_text(json.dumps(data))


def main():
    registered_tickets = load_db()
    kname = os.environ["KNAME"]
    kid = os.environ["KID"]
    kphone = os.environ["KPHONE"]
    kmail = os.environ["KMAIL"]
    while True:
        try:
            for event_info in get_event_info():
                event_id = event_info["event"]["_id"]
                print("event_id: {}".format(event_id))
                tickets = get_ticket_types(event_id)
                ticket_id = tickets['ticketTypes'][0]['_id']
                if tickets["ticketTypes"][0]["price"] != 0:
                    # Its not a free ticket skip
                    print("Not a free ticket skipping")
                    continue
                print("ticket_id: {}".format(ticket_id))
                if ticket_id not in registered_tickets:
                    ret_val = do_register(kname, kid, kphone,
                                          kmail, "1999-04-14T21:00:00.000Z", 24, event_info, tickets)
                    registered_tickets.append(ticket_id)
                    write_db(registered_tickets)
        except Exception as e:
            print('Error: ', e.__class__.__name__)
            print(e)
        print("Waiting 60 min")
        time.sleep(60 * 60)


if __name__ == "__main__":
    main()
