#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate complete, 100% synchronized TypeScript locale files for SpaceLoop:
- en.ts
- hi.ts
- mr.ts
- gar.ts
- kfy.ts
- jns.ts
"""

import os
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOCALES_DIR = os.path.join(ROOT, 'frontend', 'src', 'i18n', 'locales')

from generate_locales_json import get_locales
from build_locales_dataset import common_en, common_hi, common_mr, common_gar, common_kfy, common_jns

base_locales = get_locales()
en = base_locales["en"]
hi = base_locales["hi"]

def translate_structure(target_common, lang_code, translations_override=None):
    # Deep copy structure from hi/en and apply locale-specific dialect tokens
    res = {}
    for section, sec_data in hi.items():
        res[section] = {}
        for k, v in sec_data.items():
            if section == "common":
                res[section][k] = target_common.get(k, v)
            elif isinstance(v, dict):
                res[section][k] = {}
                for sub_k, sub_v in v.items():
                    res[section][k][sub_k] = sub_v
            else:
                res[section][k] = v

    if translations_override:
        for sec, kvs in translations_override.items():
            if sec not in res:
                res[sec] = {}
            for k, v in kvs.items():
                res[sec][k] = v
    return res

# Marathi translations
mr_overrides = {
    "nav": {
        "explore": "जागा शोधा",
        "howItWorks": "हे कसे कार्य करते",
        "calculator": "उत्पन्न कॅल्क्युलेटर",
        "listSpace": "जागा सूचीबद्ध करा",
        "trustSafety": "विश्वास आणि सुरक्षा",
        "architecture": "आर्किटेक्चर",
        "myBookings": "माझे बुकिंग",
        "hostDashboard": "होस्ट डॅशबोर्ड",
        "seekerPortal": "सीकर पोर्टल",
        "hostPortal": "होस्ट पोर्टल",
        "switchToSeeker": "सीकर मोडवर स्विच करा",
        "switchToHost": "होस्ट मोडवर स्विच करा",
        "signIn": "साइन इन करा",
        "signOut": "साइन आउट",
        "signUp": "साइन अप करा",
        "register": "नोंदणी करा",
        "profile": "प्रोफाइल",
        "language": "भाषा",
        "theme": "थीम",
        "notifications": "सूचना",
        "help": "मदत आणि सामान्य प्रश्न",
        "support": "सपोर्ट",
        "settings": "सेटिंग्ज",
        "menu": "मेनू",
        "closeMenu": "मेनू बंद करा",
        "activeBookingsBadge": "{count} सक्रिय"
    },
    "hero": {
        "networkBadge": "भारताचे पहिले एआय-सक्षम मायक्रो-स्पेस नेटवर्क",
        "teamBadge": "आर्किटेक्चर आणि टीम →",
        "headline": "न वापरलेल्या जागेचे",
        "highlight": "जिवंत संधीमध्ये रूपांतर करा.",
        "subtitle": "रिमोट काम, क्लायंट मीटिंग, क्रिएटिव्ह स्टुडिओ, कार्यशाळा आणि अभ्यासासाठी सत्यापित जागा शोधा आणि बुक करा — प्रति तास तत्वावर. नैसर्गिक भाषा एआय जुळणी, त्वरित मायक्रो-लीज आणि शून्य-हार्डवेअर क्यूआर प्रवेशासह.",
        "searchPlaceholder": "शहर, जागेचा प्रकार किंवा उपक्रमानुसार शोधा (उदा. पुणे डेस्क, मीटिंग रूम)...",
        "findSpaceBtn": "जागा शोधा →",
        "listSpaceBtn": "होस्ट बना / होस्ट ओएस",
        "popularTags": "लोकप्रिय: पुणे डेस्क, खराडी स्टुडिओ, मुंबई मीटिंग, डेहराडून ऑफिस",
        "quickStats": "भारताचे पहिले एआय-सक्षम मायक्रो-स्पेस नेटवर्क",
        "instantEscrowBadge": "₹100 यूपीआय मायक्रो-एस्क्रो",
        "zeroHardwareBadge": "त्वरित क्यूआर / जीपीएस अनलॉक",
        "sec52Badge": "कायदेशीर भारतीय सुखाधिकार भाडेपट्टा",
        "digilockerBadge": "डिजीलॉकर केवायसी सत्यापित",
        "startingRateLabel": "सुरुवातीचे प्रति तास दर",
        "discomVerifiedLabel": "डिस्कॉम मीटर सत्यापित",
        "instantLeaseLabel": "30 सेकंद त्वरित एआय मायक्रो-लीज",
        "escrowReleaseLabel": "यूपीआय एस्क्रो ऑटो-रिलीज"
    },
    "landing": {
        "howItWorksBadge": "स्पेस लूप कसे कार्य करते",
        "howItWorksTitle": "शोधापासून ते चेकआउटपर्यंत सहा सोप्या पायऱ्या.",
        "howItWorksSubtitle": "आधुनिक भारतासाठी डिझाइन केलेला घर्षणरहित, कायदेशीरदृष्ट्या सुरक्षित पी2पी लीजिंग वर्कफ्लो.",
        "step1Title": "1. शोधा (Discover)",
        "step1Desc": "लूपबॉटला सांगा किंवा नैसर्गिक भाषेत शोधा — डेस्क, स्टुडिओ, मीटिंग रूम किंवा शांत अभ्यास कक्ष.",
        "step2Title": "2. जुळवा (Match)",
        "step2Desc": "एआय अंतर, ध्वनी स्तर (dB), सुविधा आणि प्रति तास बजेटनुसार एकत्रित स्कोअर काढते.",
        "step3Title": "3. बुक करा (Book)",
        "step3Desc": "कलम 52 अंतर्गत स्वयंचलित मायक्रो-लीज आणि ₹100 यूपीआय होल्डसह त्वरित बुक करा.",
        "step4Title": "4. डिजिटल स्वाक्षरी (Sign)",
        "step4Desc": "भारतीय सुखाधिकार कायद्यानुसार डिजिटल परवाना — शून्य भाडेकरू हक्क, 100% कायदेशीर स्पष्टता.",
        "step5Title": "5. प्रवेश (Access)",
        "step5Desc": "हार्डवेअर-मुक्त आगमन. दरवाजाचा क्यूआर स्कॅन करा किंवा जीपीएस पुष्टीवर अनलॉक टॅप करा.",
        "step6Title": "6. पूर्ण व परतावा (Complete)",
        "step6Desc": "अटींच्या तपासणीसह सत्र समाप्त करा. 120 सेकंदांत एस्क्रो थेट तुमच्या यूपीआय खात्यात परत.",
        "dualAudienceTitle": "स्पेस अर्थव्यवस्थेच्या दोन्ही बाजूंच्या फायद्यासाठी",
        "seekerBadge": "क्रिएटर्स, रिमोट कर्मचारी आणि टीम्ससाठी",
        "seekerTitle": "मागणीनुसार व्यावसायिक कार्यक्षेत्र",
        "seekerSubtitle": "दीर्घकालीन करारांशिवाय प्रति तास खाजगी डेस्क, क्लायंट मीटिंग रूम आणि प्रॉडक्शन स्टुडिओ बुक करा.",
        "seekerBullet1": "प्रति तास मायक्रो-बुकिंग — कोणतीही मासिक बंधने नाहीत",
        "seekerBullet2": "ध्वनी, प्रकाश आणि वाय-फाय टेलिमेट्री सत्यापित खोल्या",
        "seekerBullet3": "स्मार्ट क्यूआर / जीपीएस प्रवेश — पोहोचा आणि काम सुरू करा",
        "seekerBullet4": "त्वरित परताव्यासाठी ₹100 सुरक्षित एस्क्रो होल्ड",
        "seekerCta": "सत्यापित जागा एक्सप्लोर करा →",
        "hostBadge": "जागा मालकांसाठी",
        "hostTitle": "निष्क्रिय क्षमतेचे उत्पन्नात रूपांतर करा",
        "hostSubtitle": "स्वयंचलित कायदेशीर संरक्षणासह रिक्त डेस्क, मीटिंग रूम, स्टुडिओ आणि टेरेसचे कमाईत रूपांतर करा.",
        "hostBullet1": "रिक्त खोल्या, डेस्क, स्टुडिओ किंवा छताची काही मिनिटांत नोंदणी करा",
        "hostBullet2": "कलम 52 कायदेशीर संरक्षण — शून्य प्रतिकूल ताबा जोखीम",
        "hostBullet3": "दरवाजा क्यूआर आणि जीपीएस फेंसिंगसह स्वयंचलित चेक-इन",
        "hostBullet4": "एकूण कमाईचा 95% थेट यूपीआय पेआउट",
        "hostCta": "होस्ट ओएस मध्ये जागा नोंदवा →",
        "trustBadge": "डिझाइनद्वारे विश्वास आणि सुरक्षा",
        "trustTitle": "इंडिया स्टॅक टेलिमेट्रीसह विकसित",
        "trustSubtitle": "स्पेस लूपवरील प्रत्येक संवाद सार्वभौम ओळख, कायदेशीर परवाना आणि आर्थिक हमीद्वारे संरक्षित आहे.",
        "trustCard1Title": "डिजीलॉकर ड्युअल केवायसी",
        "trustCard1Desc": "256-बिट सुरक्षित हॅशसह साधक आणि होस्ट दोघांची ओळख टोकनाइज्ड. कोणताही कच्चा डेटा साठवला जात नाही.",
        "trustCard2Title": "डिस्कॉम परिसर पुरावा",
        "trustCard2Desc": "होस्ट परिसराचे वीज डिस्कॉम मीटर (CA) नोंदीद्वारे सत्यापन, बनावट सूचींवर पूर्ण बंदी.",
        "trustCard3Title": "कायदेशीर मायक्रो-लीज",
        "trustCard3Desc": "भारतीय सुखाधिकार कायदा कलम 52 अंतर्गत लागू करण्यायोग्य तात्पुरता परवाना कोणत्याही भाडेकरू अधिकारांशिवाय.",
        "featuredBadge": "खास निवड",
        "featuredTitle": "वैशिष्ट्यीकृत मायक्रो-जागा",
        "featuredSubtitle": "त्वरित प्रति तास बुकिंगसाठी तयार सर्वोच्च रेटेड, टेलिमेट्री-सत्यापित जागा एक्सप्लोर करा.",
        "ctaTitle": "स्पेस लूपचा अनुभव घेण्यासाठी सज्ज आहात का?",
        "ctaSubtitle": "संपूर्ण भारतातील भौतिक जागा अनलॉक करणाऱ्या हजारो होस्ट आणि व्यावसायिकांमध्ये सामील व्हा.",
        "ctaSeekerBtn": "आता जागा शोधा",
        "ctaHostBtn": "होस्ट ओएस मध्ये जागा नोंदवा"
    },
    "architect": {
        "badge": "4 मुख्य आर्किटेक्ट्स",
        "heroTitle": "स्पेस लूपच्या निर्मात्या आर्किटेक्ट्सना भेटा",
        "heroQuote": "“चार मने. एक ध्येय. प्रत्येक योग्य जागेचा स्मार्ट वापर करणे.”",
        "heroDesc": "भारतातील अग्रगण्य पीअर-टू-पीअर भौतिक स्पेस मार्केटप्लेसची रचना, निर्मिती आणि सुरक्षा करणारी चार सदस्यीय अभियांत्रिकी टीम.",
        "telemetryProtocol": "प्रोटोकॉल",
        "telemetryProtocolVal": "कलम 52 भारतीय सुखाधिकार",
        "telemetryAi": "एआय राउटिंग",
        "telemetryAiVal": "ग्रोक 120बी + जेमिनी फेलओव्हर",
        "telemetrySovereignty": "सार्वभौमत्व",
        "telemetrySovereigntyVal": "डीपीडीपी कायदा 2023 टोकनाइज्ड",
        "telemetryEscrow": "एस्क्रो होल्ड",
        "telemetryEscrowVal": "₹100 एनपीसीआय मायक्रो-एस्क्रो",
        "coreArchitectsTitle": "मुख्य सिस्टम आर्किटेक्ट्स",
        "inspectSpecs": "वैशिष्ट्ये तपासा",
        "domainLabel": "कार्यक्षेत्र:",
        "email": "ईमेल",
        "linkedIn": "लिंक्डइन",
        "subsystemSpec": "सबसिस्टम आर्किटेक्चर तपशील",
        "slot": "स्लॉट",
        "primarySubsystem": "प्राथमिक सबसिस्टम",
        "archCapabilities": "आर्किटेक्चरल क्षमता:",
        "techStack": "तंत्रज्ञान स्टॅक:",
        "sendDirectEmail": "थेट ईमेल पाठवा",
        "linkedInProfile": "लिंक्डइन प्रोफाइल",
        "closeInspector": "इन्स्पेक्टर बंद करा",
        "finaleBadge": "हॅकाथॉन भव्य समारोप // उत्पादन सज्ज",
        "finaleTitle": "सामायिक भौतिक जागांच्या भविष्याची निर्मिती",
        "finaleDesc": "स्पेस लूप शून्य-हार्डवेअर स्मार्ट ऍक्सेस, कलम 52 अंतर्गत स्वयंचलित मायक्रो-लीज आणि सार्वभौम ओळख पडताळणीद्वारे भारतातील रिक्त क्षमता खुली करते.",
        "exploreMarketplace": "मार्केटप्लेस एक्सप्लोर करा",
        "returnHome": "मुख्यपृष्ठावर परत जा"
    }
}

# Garhwali overrides
gar_overrides = {
    "nav": {
        "explore": "जगा खोजा",
        "howItWorks": "ये कु काम कना च",
        "calculator": "आमदनी कैलकुलेटर",
        "listSpace": "जगा जोड़ो",
        "trustSafety": "भरोसा अर सुरक्षा",
        "architecture": "आर्किटेक्चर",
        "myBookings": "म्यर बुकिंग",
        "hostDashboard": "होस्ट डैशबोर्ड",
        "seekerPortal": "सीकर पोर्टल",
        "hostPortal": "होस्ट पोर्टल",
        "switchToSeeker": "सीकर मोड म जावा",
        "switchToHost": "होस्ट मोड म जावा",
        "signIn": "साइन इन करा",
        "signOut": "साइन आउट",
        "signUp": "साइन अप करा",
        "register": "खाता बणावा",
        "profile": "प्रोफ़ाइल",
        "language": "भाषा",
        "theme": "रंग रूप",
        "notifications": "सूचना",
        "help": "मदद अर सवाल",
        "support": "सहयोग",
        "settings": "सेटिंग",
        "menu": "मेनू",
        "closeMenu": "मेनू बंद करा",
        "activeBookingsBadge": "{count} चालू"
    },
    "hero": {
        "networkBadge": "भारत कु पैलु एआई-संचालित माइक्रो-स्पेस नेटवर्क",
        "teamBadge": "आर्किटेक्चर अर टीम →",
        "headline": "खाली पड़ी जगा तैं",
        "highlight": "जीवंत अवसर म बदलो।",
        "subtitle": "रिमोट काम, ग्राहक मुलाकात, क्रिएटिव स्टूडियो, वर्कशॉप अर पढ़ाई खातिर जांची-परखी जगा खोजा अर बुक करा — घंटावार हिसाब से। प्राकृतिक बोली एआई मिलान, झटपट माइक्रो-लीज अर बिना हार्डवेयर क्यूआर एक्सेस का दगड़ि।",
        "searchPlaceholder": "शहर, जगा कु प्रकार या काम से खोजा (उदा. देहरादून डेस्क, मीटिंग रूम)...",
        "findSpaceBtn": "जगा खोजा →",
        "listSpaceBtn": "होस्ट बणा / होस्ट ओएस",
        "popularTags": "मशहूर: देहरादून डेस्क, राजपुर स्टूडियो, ऋषिकेश मीटिंग, हरिद्वार ऑफिस",
        "quickStats": "भारत कु पैलु एआई-संचालित माइक्रो-स्पेस नेटवर्क",
        "instantEscrowBadge": "₹100 यूपीआई माइक्रो-एस्क्रो",
        "zeroHardwareBadge": "झटपट क्यूआर / जीपीएस अनलॉक",
        "sec52Badge": "धारा 52 कानूनी सुखाधिकार लीज",
        "digilockerBadge": "डिजीलॉकर केवाईसी सत्यापित",
        "startingRateLabel": "सुरुआती प्रति घंटा दर",
        "discomVerifiedLabel": "डिस्कॉम मीटर सत्यापित",
        "instantLeaseLabel": "30 सेकंड म झटपट एआई माइक्रो-लीज",
        "escrowReleaseLabel": "यूपीआई एस्क्रो स्वतः रिलीज"
    },
    "landing": {
        "howItWorksBadge": "स्पेस लूप कना काम करद",
        "howItWorksTitle": "खोज से लिकै चेकआउट तलक छह सीधा कदम।",
        "howItWorksSubtitle": "आधुनिक भारत खातिर बणायीं बिना रुकावट, कानूनी रूप से पक्की पी2पी लीजिंग व्यवस्था।",
        "step1Title": "1. खोजा (Discover)",
        "step1Desc": "लूपबॉट तैं बताओ या अपणी भाषा म खोजा — डेस्क, स्टूडियो, मीटिंग रूम या शांत पढ़ाई कु जागो।",
        "step2Title": "2. मिलान करा (Match)",
        "step2Desc": "एआई दूरी, आवाज स्तर (dB), सुविधा अर घंटावार बजेट कु हिसाब से स्कोअर बणौंद।",
        "step3Title": "3. बुक करा (Book)",
        "step3Desc": "धारा 52 का तहत बिना देरी ₹100 यूपीआई होल्ड का दगड़ि तुरंत बुक करा।",
        "step4Title": "4. डिजिटल हस्ताक्षर (Sign)",
        "step4Desc": "भारतीय सुखाधिकार अधिनियम का तहत त्वरित कानूनी लाइसेंस — कब्ज़ा कु शून्य खतरा।",
        "step5Title": "5. दाखिला (Access)",
        "step5Desc": "बिना ताला-चाबी आगमन। द्वार कु क्यूआर कोड स्कैन करा या जीपीएस से तुरंत खोलो।",
        "step6Title": "6. पुरा अर रिफंड (Complete)",
        "step6Desc": "कमरा जांची क सत्र खत्म करा। 120 सेकंड म ₹100 एस्क्रो सीधे यूपीआई म वापस।",
        "dualAudienceTitle": "जगा कु जरूरत अर जगा कु मालिक दोनों खातिर",
        "seekerBadge": "क्रिएटर्स, रिमोट कामगार अर टीमूं खातिर",
        "seekerTitle": "मांग पर बढ़िया काम कु जागो",
        "seekerSubtitle": "बिना लामे समय का बंधन, घंटावार हिसाब से प्राइवेट डेस्क, मीटिंग रूम अर स्टूडियो बुक करा।",
        "seekerBullet1": "घंटावार माइक्रो-बुकिंग — कोई मैना भर कु बंधन नी",
        "seekerBullet2": "आवाज, उज्याळ अर वाई-फाई टेलीमेट्री जांची कमरा",
        "seekerBullet3": "स्मार्ट क्यूआर / जीपीएस प्रवेश — पहुंचा अर काम शुरू करा",
        "seekerBullet4": "झटपट वापसी दगड़ि ₹100 सुरक्षित एस्क्रो होल्ड",
        "seekerCta": "जांची-परखी जगा खोजा →",
        "hostBadge": "जमीन-जागा का मालिकूं खातिर",
        "hostTitle": "खाली जगा से आमदनी बणावा",
        "hostSubtitle": "कानूनी सुरक्षा का दगड़ि खाली डेस्क, कमरा, स्टूडियो या छत बटि पक्की आमदनी कमावा।",
        "hostBullet1": "खाली कमरा, डेस्क, स्टूडियो या छत मिनटों म लिस्ट करा",
        "hostBullet2": "धारा 52 कानूनी सुरक्षा — कब्ज़ा कु शून्य खतरा",
        "hostBullet3": "द्वार क्यूआर अर जीपीएस फेंसिंग से स्वतः चेक-इन",
        "hostBullet4": "कुल कमाई कु 95% सीधा यूपीआई खाता म",
        "hostCta": "होस्ट ओएस म जगा जोड़ो →",
        "trustBadge": "पक्का भरोसा अर सुरक्षा",
        "trustTitle": "इंडिया स्टैक टेलीमेट्री दगड़ि तैयार",
        "trustSubtitle": "स्पेस लूप पर हर लेन-देन असली पहचान, कानूनी लाइसेंस अर सुरक्षित भुगतान दगड़ि पक्को च।",
        "trustCard1Title": "डिजीलॉकर डुअल केवाईसी",
        "trustCard1Desc": "256-बिट सुरक्षित टोकन दगड़ि ग्राहक अर मालिक दोनों की पहचान पक्की। कुई कच्चू डेटा नी राखेंद।",
        "trustCard2Title": "डिस्कॉम मीटर सबूत",
        "trustCard2Desc": "बिजली डिस्कॉम मीटर (CA) रिकॉर्ड से जगा कु असली सत्यापन, झूठी लिस्टिंग पर रोक।",
        "trustCard3Title": "कानूनी माइक्रो-लीज",
        "trustCard3Desc": "भारतीय सुखाधिकार अधिनियम धारा 52 का तहत बिना किरायेदारी अधिकार अस्थायी कानूनी लाइसेंस।",
        "featuredBadge": "खास चुनीं जगा",
        "featuredTitle": "खास माइक्रो-स्थान",
        "featuredSubtitle": "तुरंत घंटावार बुकिंग खातिर तैयार बढ़िया, टेलीमेट्री जांची-परखी जगा देखा।",
        "ctaTitle": "स्पेस लूप कु इस्तेमाल करणा खातिर तैयार छा?",
        "ctaSubtitle": "पूरा भारत म खाली जगा तैं आमदनी म बदलन्या हजारूं साथियूं दगड़ि जुड़ा।",
        "ctaSeekerBtn": "अबि जगा खोजा",
        "ctaHostBtn": "होस्ट ओएस म जगा जोड़ो"
    },
    "architect": {
        "badge": "4 मुख्य आर्किटेक्ट्स",
        "heroTitle": "स्पेस लूप बणौण्या आर्किटेक्ट्स से मिला",
        "heroQuote": "“चार दिमाग। एक ध्येय। हर काम की जगा तैं होशियार बणाण।”",
        "heroDesc": "भारत कु पैलु पीयर-टू-पीयर फिजिकल स्पेस मार्केटप्लेस तैं बणौण्या अर सुरक्षित रखण्या चार सदस्यीय इंजीनियरिंग टीम।",
        "telemetryProtocol": "प्रोटोकॉल",
        "telemetryProtocolVal": "धारा 52 भारतीय सुखाधिकार",
        "telemetryAi": "एआई रूटिंग",
        "telemetryAiVal": "ग्रोक 120बी + जेमिनी फेलओवर",
        "telemetrySovereignty": "संप्रभुता",
        "telemetrySovereigntyVal": "डीपीडीपी कानून 2023 टोकनाइज्ड",
        "telemetryEscrow": "एस्क्रो होल्ड",
        "telemetryEscrowVal": "₹100 एनपीसीआई माइक्रो-एस्क्रो",
        "coreArchitectsTitle": "मुख्य सिस्टम आर्किटेक्ट्स",
        "inspectSpecs": "विस्तार देखा",
        "domainLabel": "कार्यक्षेत्र:",
        "email": "ईमेल",
        "linkedIn": "लिंक्डइन",
        "subsystemSpec": "सबसिस्टम आर्किटेक्चर विस्तार",
        "slot": "स्लॉट",
        "primarySubsystem": "प्राथमिक सबसिस्टम",
        "archCapabilities": "आर्किटेक्चरल क्षमता:",
        "techStack": "तकनीकी स्टैक:",
        "sendDirectEmail": "सीधा ईमेल भेजो",
        "linkedInProfile": "लिंक्डइन प्रोफाइल",
        "closeInspector": "इंस्पेक्टर बंद करा",
        "finaleBadge": "हैकाथॉन भव्य समापन // उत्पादन तैयार",
        "finaleTitle": "साझा भौतिक जागा का भविष्य कु निर्माण",
        "finaleDesc": "स्पेस लूप बिना चाबी-ताला स्मार्ट प्रवेश, धारा 52 कानूनी लीज अर असली पहचान से खाली पड़ी जगा तैं आबाद करद।",
        "exploreMarketplace": "मार्केटप्लेस देखा",
        "returnHome": "होम म पाछा जावा"
    }
}

# Kumaoni overrides
kfy_overrides = {
    "nav": {
        "explore": "जागा खोजा",
        "howItWorks": "यै कसिक काम करँछ",
        "calculator": "कमाई कैलकुलेटर",
        "listSpace": "जागा जोड़ो",
        "trustSafety": "भरोस और सुरक्षा",
        "architecture": "आर्किटेक्चर",
        "myBookings": "म्यर बुकिंग",
        "hostDashboard": "होस्ट डैशबोर्ड",
        "seekerPortal": "सीकर पोर्टल",
        "hostPortal": "होस्ट पोर्टल",
        "switchToSeeker": "सीकर मोड ल जावा",
        "switchToHost": "होस्ट मोड ल जावा",
        "signIn": "साइन इन करा",
        "signOut": "साइन आउट",
        "signUp": "साइन अप करा",
        "register": "खाता बणाओ",
        "profile": "प्रोफ़ाइल",
        "language": "भाषा",
        "theme": "थीम",
        "notifications": "सूचना",
        "help": "मदद और सवाल",
        "support": "सहयोग",
        "settings": "सेटिंग",
        "menu": "मेनू",
        "closeMenu": "मेनू बंद करा",
        "activeBookingsBadge": "{count} चालू"
    },
    "hero": {
        "networkBadge": "भारत क पैल एआई-संचालित माइक्रो-स्पेस नेटवर्क",
        "teamBadge": "आर्किटेक्चर और टीम →",
        "headline": "खाली पड़ि जगा के",
        "highlight": "जीवन भरुक मौक़ा म बदलो।",
        "subtitle": "रिमोट काम, ग्राहक मुलाक़ात, क्रिएटिव स्टूडियो, वर्कशॉप और पढ़ाई खातिर जांची-परखी जागा खोजा और बुक करा — घंटावार हिसाब ल। प्राकृतिक बोली एआई मिलान, त्वरित माइक्रो-लीज और बिना हार्डवेयर क्यूआर एक्सेस दगड़।",
        "searchPlaceholder": "शहर, जागा क प्रकार या काम ल खोजा (उदा. नैनीताल डेस्क, मीटिंग रूम)...",
        "findSpaceBtn": "जागा खोजा →",
        "listSpaceBtn": "होस्ट बणो / होस्ट ओएस",
        "popularTags": "मशहूर: नैनीताल डेस्क, हल्द्वानी स्टूडियो, अल्मोड़ा मीटिंग, देहरादून ऑफिस",
        "quickStats": "भारत क पैल एआई-संचालित माइक्रो-स्पेस नेटवर्क",
        "instantEscrowBadge": "₹100 यूपीआई माइक्रो-एस्क्रो",
        "zeroHardwareBadge": "तुरंत क्यूआर / जीपीएस अनलॉक",
        "sec52Badge": "धारा 52 कानूनी सुखाधिकार लीज",
        "digilockerBadge": "डिजीलॉकर केवाईसी सत्यापित",
        "startingRateLabel": "सुरुवाती प्रति घंटा दर",
        "discomVerifiedLabel": "डिस्कॉम मीटर सत्यापित",
        "instantLeaseLabel": "30 सेकंड म त्वरित एआई माइक्रो-लीज",
        "escrowReleaseLabel": "यूपीआई एस्क्रो स्वतः रिलीज"
    },
    "landing": {
        "howItWorksBadge": "स्पेस लूप कसिक काम करँछ",
        "howItWorksTitle": "खोज बटी चेकआउट तलक छह आसान कदम।",
        "howItWorksSubtitle": "आधुनिक भारत खातिर बणायीं बिना रुकावट, कानूनी रूप ल पक्की पी2पी लीजिंग व्यवस्था।",
        "step1Title": "1. खोजा (Discover)",
        "step1Desc": "लूपबॉट क बताओ या अपणि भाषा म खोजा — डेस्क, स्टूडियो, मीटिंग सुइट या शांत पढ़ाई क जाग।",
        "step2Title": "2. मिलान करा (Match)",
        "step2Desc": "एआई दूरी, आवाज क स्तर (dB), सुविधा और प्रति घंटा बजट क हिसाब ल स्कोअर बणाँछ।",
        "step3Title": "3. बुक करा (Book)",
        "step3Desc": "धारा 52 क तहत बिना देरी ₹100 यूपीआई होल्ड क दगड़ त्वरित बुक करा।",
        "step4Title": "4. डिजिटल हस्ताक्षर (Sign)",
        "step4Desc": "भारतीय सुखाधिकार कानून क तहत डिजिटल लाइसेंस — किराएदारी कब्ज़ क शून्य खतरा।",
        "step5Title": "5. प्रवेश (Access)",
        "step5Desc": "बिना हार्डवेयर प्रवेश। द्वार क क्यूआर कोड स्कैन करा या जीपीएस पुष्टी ल खोलो।",
        "step6Title": "6. पूर और रिफंड (Complete)",
        "step6Desc": "कमरा क जांच दगड़ सत्र समाप्त करा। 120 सेकंड भितर ₹100 एस्क्रो सीधैं यूपीआई म वापस।",
        "dualAudienceTitle": "जागा क जरूरत और जागा क मालिक दोनों खातिर",
        "seekerBadge": "क्रिएटर्स, रिमोट काम करन्या और टीमूं खातिर",
        "seekerTitle": "मांग पर पेशेवर कामुक जाग",
        "seekerSubtitle": "बिना लम्बा समय क बंधन, घंटावार हिसाब ल प्राइवेट डेस्क, मीटिंग रूम और स्टूडियो बुक करा।",
        "seekerBullet1": "घंटावार माइक्रो-बुकिंग — कोई महिना भरुक बंधन नी",
        "seekerBullet2": "आवाज, घाम और वाई-फाई टेलीमेट्री जांची कमरा",
        "seekerBullet3": "स्मार्ट क्यूआर / जीपीएस प्रवेश — पहुंचा और काम शुरू करा",
        "seekerBullet4": "त्वरित वापसी दगड़ ₹100 सुरक्षित एस्क्रो होल्ड",
        "seekerCta": "जांची-परखी जागा खोजा →",
        "hostBadge": "प्रॉपर्टी और जागा मालिकूं खातिर",
        "hostTitle": "खाली जागा बटी आमदनी कमाओ",
        "hostSubtitle": "कानूनी सुरक्षा क दगड़ खाली डेस्क, कमरा, स्टूडियो या छत बटी पक्की आमदनी कमाओ।",
        "hostBullet1": "खाली कमरा, डेस्क, स्टूडियो या छत मिनटों म लिस्ट करा",
        "hostBullet2": "धारा 52 कानूनी सुरक्षा — कब्ज़ क शून्य खतरा",
        "hostBullet3": "द्वार क्यूआर और जीपीएस फेंसिंग ल स्वतः चेक-इन",
        "hostBullet4": "कुल कमाई क 95% सीधैं यूपीआई खाता म",
        "hostCta": "होस्ट ओएस म जागा जोड़ो →",
        "trustBadge": "पक्को भरोस और सुरक्षा",
        "trustTitle": "इंडिया स्टैक टेलीमेट्री दगड़ तैयार",
        "trustSubtitle": "स्पेस लूप पर हर लेन-देन असली पहचान, कानूनी लाइसेंस और सुरक्षित भुगतान दगड़ पक्को छ।",
        "trustCard1Title": "डिजीलॉकर डुअल केवाईसी",
        "trustCard1Desc": "256-बिट सुरक्षित टोकन दगड़ ग्राहक और मालिक दोनों क पहचान पक्की। कच्चू डेटा नी राखिँछ।",
        "trustCard2Title": "डिस्कॉम मीटर सबूत",
        "trustCard2Desc": "बिजली डिस्कॉम मीटर (CA) रिकॉर्ड ल जागा क असली सत्यापन, झूठी लिस्टिंग पर रोक।",
        "trustCard3Title": "कानूनी माइक्रो-लीज",
        "trustCard3Desc": "भारतीय सुखाधिकार कानून धारा 52 क तहत बिना किरायेदारी अधिकार अस्थायी कानूनी लाइसेंस।",
        "featuredBadge": "खास चुनीं जागा",
        "featuredTitle": "खास माइक्रो-जागा",
        "featuredSubtitle": "तुरंत घंटावार बुकिंग खातिर तैयार बढ़िया, टेलीमेट्री जांची-परखी जागा देखा।",
        "ctaTitle": "स्पेस लूप क अनुभव करणा खातिर तैयार छा?",
        "ctaSubtitle": "पूरा भारत म खाली जागा क आमदनी म बदलन्या हजारूं साथियूं दगड़ जुड़ा।",
        "ctaSeekerBtn": "अभि जागा खोजा",
        "ctaHostBtn": "होस्ट ओएस म जागा जोड़ो"
    },
    "architect": {
        "badge": "4 मुख्य आर्किटेक्ट्स",
        "heroTitle": "स्पेस लूप बणाण वाल आर्किटेक्ट्स से मिला",
        "heroQuote": "“चार दिमाग। एक ध्येय। हर काम क जाग क स्मार्ट बणाण।”",
        "heroDesc": "भारत क पैल पीयर-टू-पीयर फिजिकल स्पेस मार्केटप्लेस क बणाण और सुरक्षित रखण वाल चार सदस्यीय इंजीनियरिंग टीम।",
        "telemetryProtocol": "प्रोटोकॉल",
        "telemetryProtocolVal": "धारा 52 भारतीय सुखाधिकार",
        "telemetryAi": "एआई रूटिंग",
        "telemetryAiVal": "ग्रोक 120बी + जेमिनी फेलओवर",
        "telemetrySovereignty": "संप्रभुता",
        "telemetrySovereigntyVal": "डीपीडीपी कानून 2023 टोकनाइज्ड",
        "telemetryEscrow": "एस्क्रो होल्ड",
        "telemetryEscrowVal": "₹100 एनपीसीआई माइक्रो-एस्क्रो",
        "coreArchitectsTitle": "मुख्य सिस्टम आर्किटेक्ट्स",
        "inspectSpecs": "विस्तार देखा",
        "domainLabel": "कार्यक्षेत्र:",
        "email": "ईमेल",
        "linkedIn": "लिंक्डइन",
        "subsystemSpec": "सबसिस्टम आर्किटेक्चर विस्तार",
        "slot": "स्लॉट",
        "primarySubsystem": "प्राथमिक सबसिस्टम",
        "archCapabilities": "आर्किटेक्चरल क्षमता:",
        "techStack": "तकनीकी स्टैक:",
        "sendDirectEmail": "सीधा ईमेल भेजो",
        "linkedInProfile": "लिंक्डइन प्रोफाइल",
        "closeInspector": "इंस्पेक्टर बंद करा",
        "finaleBadge": "हैकाथॉन भव्य समापन // उत्पादन तैयार",
        "finaleTitle": "साझा भौतिक जागा क भविष्य क निर्माण",
        "finaleDesc": "स्पेस लूप बिना चाबी-ताला स्मार्ट प्रवेश, धारा 52 कानूनी लीज और असली पहचान ल खाली पड़ि जागा क आबाद करँछ।",
        "exploreMarketplace": "मार्केटप्लेस देखा",
        "returnHome": "होम म पाछा जावा"
    }
}

# Jaunsari overrides
jns_overrides = {
    "nav": {
        "explore": "जगहा खोजा",
        "howItWorks": "यो काम केन्करे",
        "calculator": "कमाई कैलकुलेटर",
        "listSpace": "जगहा जोड़ो",
        "trustSafety": "भरोसो और सुरक्षा",
        "architecture": "आर्किटेक्चर",
        "myBookings": "मारी बुकिंग",
        "hostDashboard": "होस्ट डैशबोर्ड",
        "seekerPortal": "सीकर पोर्टल",
        "hostPortal": "होस्ट पोर्टल",
        "switchToSeeker": "सीकर मोड ल जावा",
        "switchToHost": "होस्ट मोड ल जावा",
        "signIn": "साइन इन करा",
        "signOut": "साइन आउट",
        "signUp": "साइन अप करा",
        "register": "खातो बणावा",
        "profile": "प्रोफ़ाइल",
        "language": "बोली/भाषा",
        "theme": "थीम",
        "notifications": "सूचना",
        "help": "मदद और सवाल",
        "support": "सहयोग",
        "settings": "सेटिंग",
        "menu": "मेनू",
        "closeMenu": "मेनू बंद करा",
        "activeBookingsBadge": "{count} चालू"
    },
    "hero": {
        "networkBadge": "भारत रो पैलो एआई-संचालित माइक्रो-स्पेस नेटवर्क",
        "teamBadge": "आर्किटेक्चर और टीम →",
        "headline": "खाली जगहा को",
        "highlight": "जीवंत मौक़ा म बदलो।",
        "subtitle": "रिमोट काम, ग्राहक मुलाक़ात, क्रिएटिव स्टूडियो, वर्कशॉप और पढ़ाई खातिर जांची-परखी जगहा खोजा और बुक करा — घंटावार हिसाब ल। प्राकृतिक बोली एआई मिलान, झटपट माइक्रो-लीज और बिना हार्डवेयर क्यूआर एक्सेस रा साथ।",
        "searchPlaceholder": "शहर, जगहा रो प्रकार या काम ती खोजा (उदा. चकराता डेस्क, मीटिंग रूम)...",
        "findSpaceBtn": "जगहा खोजा →",
        "listSpaceBtn": "होस्ट बणा / होस्ट ओएस",
        "popularTags": "मशहूर: चकराता डेस्क, कालसी स्टूडियो, विकासनगर मीटिंग, देहरादून ऑफिस",
        "quickStats": "भारत रो पैलो एआई-संचालित माइक्रो-स्पेस नेटवर्क",
        "instantEscrowBadge": "₹100 यूपीआई माइक्रो-एस्क्रो",
        "zeroHardwareBadge": "झटपट क्यूआर / जीपीएस अनलॉक",
        "sec52Badge": "धारा 52 कानूनी सुखाधिकार लीज",
        "digilockerBadge": "डिजीलॉकर केवाईसी सत्यापित",
        "startingRateLabel": "सुरुआती प्रति घंटा दर",
        "discomVerifiedLabel": "डिस्कॉम मीटर सत्यापित",
        "instantLeaseLabel": "30 सेकंड म झटपट एआई माइक्रो-लीज",
        "escrowReleaseLabel": "यूपीआई एस्क्रो खुद रिलीज"
    },
    "landing": {
        "howItWorksBadge": "स्पेस लूप केन्करे काम करे",
        "howItWorksTitle": "खोज ती लेके चेकआउट तक छह सीधा कदम।",
        "howItWorksSubtitle": "आधुनिक भारत खातिर बणायी बिना रुकावट, कानूनी रूप ती पक्की पी2पी लीजिंग व्यवस्था।",
        "step1Title": "1. खोजा (Discover)",
        "step1Desc": "लूपबॉट ते बताओ या सीधी भाषा म खोजा — डेस्क, स्टूडियो, मीटिंग रूम या शांत पढ़ाई री जगहा।",
        "step2Title": "2. मिलान करा (Match)",
        "step2Desc": "एआई दूरी, आवाज रो स्तर (dB), सुविधा और घंटावार बजटो रो हिसाब लगाई स्कोर दे।",
        "step3Title": "3. बुक करा (Book)",
        "step3Desc": "धारा 52 रा तहत ₹100 यूपीआई होल्ड रा साथ तुरंत बुक करा।",
        "step4Title": "4. डिजिटल दस्तखत (Sign)",
        "step4Desc": "भारतीय सुखाधिकार अधिनियम रा तहत पक्को कानूनी लाइसेंस — कब्ज़े रो कोई खतरा नी।",
        "step5Title": "5. दाखिला (Access)",
        "step5Desc": "बिना ताले-चाबी प्रवेश। द्वार रो क्यूआर स्कैन करा या जीपीएस पुष्टी ल खोलो।",
        "step6Title": "6. पुरो और रिफंड (Complete)",
        "step6Desc": "कमरा जांची क सत्र खत्म करा। 120 सेकंडा म ₹100 एस्क्रो सीधे यूपीआई म पाछो।",
        "dualAudienceTitle": "जगहा री जरूरत और जगहा रा मालिक दोनों खातिर",
        "seekerBadge": "क्रिएटर्स, रिमोट काम करन्या और टीमूं खातिर",
        "seekerTitle": "मांग पर पक्को काम री जगहा",
        "seekerSubtitle": "बिना लम्बे समय रा बंधन, घंटावार हिसाब ती प्राइवेट डेस्क, मीटिंग रूम और स्टूडियो बुक करा।",
        "seekerBullet1": "घंटावार माइक्रो-बुकिंग — कोई मैना भर रो बंधन नी",
        "seekerBullet2": "आवाज, उजाळो और वाई-फाई टेलीमेट्री जांची कमरा",
        "seekerBullet3": "स्मार्ट क्यूआर / जीपीएस प्रवेश — पहुंचा और काम शुरू करा",
        "seekerBullet4": "झटपट वापसी रा साथ ₹100 सुरक्षित एस्क्रो होल्ड",
        "seekerCta": "जांची-परखी जगहा खोजा →",
        "hostBadge": "जमीन-जगहा रा मालिकूं खातिर",
        "hostTitle": "खाली जगहा ती कमाई करा",
        "hostSubtitle": "कानूनी सुरक्षा रा साथ खाली डेस्क, कमरा, स्टूडियो या छत ती पक्की कमाई करा।",
        "hostBullet1": "खाली कमरा, डेस्क, स्टूडियो या छत मिनटों म लिस्ट करा",
        "hostBullet2": "धारा 52 कानूनी सुरक्षा — कब्ज़े रो कोई खतरा नी",
        "hostBullet3": "द्वार क्यूआर और जीपीएस फेंसिंग ती खुद चेक-इन",
        "hostBullet4": "कुल कमाई रो 95% सीधो यूपीआई खाता म",
        "hostCta": "होस्ट ओएस म जगहा जोड़ो →",
        "trustBadge": "पक्को भरोसो और सुरक्षा",
        "trustTitle": "इंडिया स्टैक टेलीमेट्री रा साथ तैयार",
        "trustSubtitle": "स्पेस लूप पर हर लेन-देन असली पहचान, कानूनी लाइसेंस और सुरक्षित भुगतान रा साथ पक्को आ।",
        "trustCard1Title": "डिजीलॉकर डुअल केवाईसी",
        "trustCard1Desc": "256-बिट सुरक्षित टोकन रा साथ ग्राहक और मालिक दोनों री पहचान पक्की। कच्चो डेटा नी राखो।",
        "trustCard2Title": "डिस्कॉम मीटर सबूत",
        "trustCard2Desc": "बिजली डिस्कॉम मीटर (CA) रिकॉर्ड ती जगहा रो असली सत्यापन, झूठी लिस्टिंग रो खात्मा।",
        "trustCard3Title": "कानूनी माइक्रो-लीज",
        "trustCard3Desc": "भारतीय सुखाधिकार अधिनियम धारा 52 रा तहत बिना किरायेदारी अधिकार अस्थायी कानूनी लाइसेंस।",
        "featuredBadge": "खास चुणी जगहा",
        "featuredTitle": "खास माइक्रो-जगहा",
        "featuredSubtitle": "तुरंत घंटावार बुकिंग खातिर तैयार बढ़िया, टेलीमेट्री जांची-परखी जगहा देखा।",
        "ctaTitle": "स्पेस लूप रो अनुभव करणा खातिर तैयार छो?",
        "ctaSubtitle": "पूरे भारत म खाली जगहा ती आमदनी बणाने वाल हजारूं साथियूं रा साथ जुड़ा।",
        "ctaSeekerBtn": "अबे जगहा खोजा",
        "ctaHostBtn": "होस्ट ओएस म जगहा जोड़ो"
    },
    "architect": {
        "badge": "4 मुख्य आर्किटेक्ट्स",
        "heroTitle": "स्पेस लूप बणाने वाल आर्किटेक्ट्स ती मिला",
        "heroQuote": "“चार दिमाग। एक मिशन। हर काम री जगहा को होशियार बणाना।”",
        "heroDesc": "भारत रो पैलो पीयर-टू-पीयर फिजिकल स्पेस मार्केटप्लेस बणाने और सुरक्षित राखने वाल चार सदस्यीय इंजीनियरिंग टीम।",
        "telemetryProtocol": "प्रोटोकॉल",
        "telemetryProtocolVal": "धारा 52 भारतीय सुखाधिकार",
        "telemetryAi": "एआई रूटिंग",
        "telemetryAiVal": "ग्रोक 120बी + जेमिनी फेलओवर",
        "telemetrySovereignty": "संप्रभुता",
        "telemetrySovereigntyVal": "डीपीडीपी कानून 2023 टोकनाइज्ड",
        "telemetryEscrow": "एस्क्रो होल्ड",
        "telemetryEscrowVal": "₹100 एनपीसीआई माइक्रो-एस्क्रो",
        "coreArchitectsTitle": "मुख्य सिस्टम आर्किटेक्ट्स",
        "inspectSpecs": "विस्तार देखा",
        "domainLabel": "कार्यक्षेत्र:",
        "email": "ईमेल",
        "linkedIn": "लिंक्डइन",
        "subsystemSpec": "सबसिस्टम आर्किटेक्चर विस्तार",
        "slot": "स्लॉट",
        "primarySubsystem": "प्राथमिक सबसिस्टम",
        "archCapabilities": "आर्किटेक्चरल क्षमता:",
        "techStack": "तकनीकी स्टैक:",
        "sendDirectEmail": "सीधा ईमेल भेजो",
        "linkedInProfile": "लिंक्डइन प्रोफाइल",
        "closeInspector": "इंस्पेक्टर बंद करा",
        "finaleBadge": "हैकाथॉन भव्य समापन // उत्पादन तैयार",
        "finaleTitle": "साझा भौतिक जगहा रा भविष्य रो निर्माण",
        "finaleDesc": "स्पेस लूप बिना चाबी-ताला स्मार्ट प्रवेश, धारा 52 कानूनी लीज और असली पहचान ती खाली पड़ी जगहा को आबाद करे।",
        "exploreMarketplace": "मार्केटप्लेस देखा",
        "returnHome": "होम म पाछो जावा"
    }
}

mr = translate_structure(common_mr, 'mr', mr_overrides)
gar = translate_structure(common_gar, 'gar', gar_overrides)
kfy = translate_structure(common_kfy, 'kfy', kfy_overrides)
jns = translate_structure(common_jns, 'jns', jns_overrides)

all_locales = {
    "en": en,
    "hi": hi,
    "mr": mr,
    "gar": gar,
    "kfy": kfy,
    "jns": jns
}

def export_ts(locale_code, data):
    ts_code = f"""import {{ TranslationDictionary }} from '../types';

export const {locale_code}: TranslationDictionary = {json.dumps(data, ensure_ascii=False, indent=2)};
"""
    file_path = os.path.join(LOCALES_DIR, f"{locale_code}.ts")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(ts_code)
    print(f"Wrote {locale_code}.ts successfully.")

for code, d in all_locales.items():
    export_ts(code, d)

print("All 6 locale files generated successfully.")
