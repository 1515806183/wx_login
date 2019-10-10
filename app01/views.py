from django.shortcuts import render,HttpResponse
import requests, time, re, json
# Create your views here.
CTIME = None
QCODE = None
TIP = 1
TICKET_DICT = {}
USER_INIT_DICT = {}
ALL_COOKIE_DICT = {}


def login(request):
    """
    获取登陆二维码
    :param request:
    :return:
    """
    global CTIME
    global QCODE
    url = 'https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&fun=new&lang=zh_CN&_=%s' % CTIME
    r = requests.get(url=url)
    v = re.findall('uuid = "(.*)";', r.text)
    QCODE = v[0]
    return render(request, 'login.html', {'qcode': QCODE})


def check_login(request):
    global TIP

    ret = {'code': 408, 'data': ''}
    # 扫码状态修改
    r1 = requests.get(url='https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid=%s&tip=%s&r=-1905574527&_=%s' % (QCODE,TIP, CTIME))

    if 'window.code=408' in r1.text:
        # 无人扫码
        return HttpResponse(json.dumps(ret))

    elif 'window.code=201' in r1.text:
        # 已扫码
        ret['code'] = '201'
        TIP = 0
        # 自己图像
        avatar = re.findall("window.userAvatar = '(.*)';", r1.text)[0]
        ret['data'] = avatar

        return HttpResponse(json.dumps(ret))

    elif 'window.code=200' in r1.text:
        # 用户已经登陆
        """
        window.code=200;
        window.redirect_uri="https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=AUYc1IV6A6jTE2KoyPg0cjyg@qrticket_0&uuid=QcxKWB9frw==&lang=zh_CN&scan=1569569606";
        """
        redirect_uri = re.findall('window.redirect_uri="(.*)";', r1.text)[0]  # 返回是的是页面
        redirect_uri += "&fun=new&version=v2&lang=zh_CN"

        # 保存cookies
        ALL_COOKIE_DICT.update(r1.cookies.get_dict())

        """
        <error>
        <ret>0</ret>
        <message></message>
        <skey>@crypt_82506aa8_f381a63ca4f3269a9f65b26734c16960</skey>
        <wxsid>ozdsfk8m7Dr4wdg0</wxsid>
        <wxuin>2970905320</wxuin>
        <pass_ticket>ndUYt3jFcjVXyti0sPdc5XxYn2vDre3%2B5OiWSbVIcvOTZUHzVd2rqomwNBuetoiE</pass_ticket>
        <isgrayscale>1</isgrayscale>
        </error>
        """
        r2 = requests.get(url=redirect_uri)  # 返回凭证
        # 凭证 提取网页数据
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r2.text, 'html.parser')
        for tag in soup.find('error').children:
            TICKET_DICT[tag.name] = tag.get_text()

        ret['code'] = 200

        ALL_COOKIE_DICT.update(r2.cookies.get_dict())

        return HttpResponse(json.dumps(ret))


def user(request):
    # 获取用户信息
    # https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-1907636977&lang=zh_CN&pass_ticket=1MzHF%252BZfP5wum4ps%252Fel8P6Xghe09HZ1DAXinaH4d%252BsbNkXv1b3fZdcly%252BtnRcyf7
    # 组织请求数据
    get_user_info_data = {
        "BaseRequest": {
            "DeviceID": "e095853846151925",
            "Sid": TICKET_DICT['wxsid'],
            "Skey": TICKET_DICT['skey'],
            "Uin": TICKET_DICT['wxuin']
        }
    }

    get_user_info_url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-1907636977&lang=zh_CN&pass_ticket=' + \
                        TICKET_DICT['pass_ticket']
    r2 = requests.post(url=get_user_info_url, json=get_user_info_data)
    r2.encoding = 'utf-8'
    user_init_dict = json.loads(r2.text)
    ALL_COOKIE_DICT.update(r2.cookies.get_dict())

    USER_INIT_DICT.update(user_init_dict)  # 存到内存里面 后面可能需要
    return render(request, 'user.html', {'user_init_dict': user_init_dict})


def contact_list(request):
    """
    查看更多联系人
    :param request:
    :return:

    https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?
    pass_ticket=NgRnjb69DcOC6PTKhnwZhee9Pqos%252B2b54HIXMOUWGSG8jpyud7bO7%252FJbUFd2oBF8&
    r=1570516888049&seq=0&
    skey=@crypt_82506aa8_a5c558ea4d57b903bea5b2346b1eaf76
    """
    ctime = str(time.time())
    base_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?pass_ticket=%s&r=%s&seq=0&skey=%s"

    url = base_url % (TICKET_DICT['pass_ticket'], ctime, TICKET_DICT['skey'])
    r = requests.get(url=url, cookies=ALL_COOKIE_DICT)
    r.encoding = 'utf-8'

    contact_list = json.loads(r.text)
    # for item in contact_list['MemberList']:
    #     print(item['UserName'], item['NickName'])

    return render(request, 'contact_list.html', {'contact_list_dict': contact_list})


def send_msg(request):
    to_user = request.GET.get('toUser')
    msg = request.GET.get('msg')

    ctime = str(int(time.time()) * 1000)
    post_dict = {
        "BaseRequest": {
            "DeviceID": "e095853846151925",
            "Sid": TICKET_DICT['wxsid'],
            "Skey": TICKET_DICT['skey'],
            "Uin": TICKET_DICT['wxuin']
        },
        'Msg': {
            "ClientMsgId": ctime,
            "Content": msg,
            'FromUserName': USER_INIT_DICT['User']['UserName'],
            "LocalID": ctime,
            "ToUserName": to_user.strip(),
            "Type": 1
        },
        "Scene": 0
    }

    url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?lang=zh_CN&pass_ticket=%s' % (TICKET_DICT['pass_ticket'],)
    # 第一种
    # r = requests.post(
    #     url=url,
    #     json=post_dict,
    #     cookies=ALL_COOKIE_DICT
    # )
    #
    # print(r.text)
    #
    # return render(request, 'send_msg.html')

    response = requests.post(url=url, data=bytes(json.dumps(post_dict, ensure_ascii=False), encoding='utf-8'))

    # print(response.text)
    # "BaseResponse": {
    #     "Ret": 0,
    #     "ErrMsg": ""
    # }
    # ,
    # "MsgID": "6873410928219600968",
    # "LocalID": "1570520960.2198744"
    # }

    return HttpResponse('ok')


def get_msg(request):
    # 1. 检查是否有消息到来,synckey(出初始化信息中获取)
    # 2. 如果 window.synccheck={retcode:"0",selector:"2"}，有消息到来
    #       ：https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid=WFKXEGSyWEgY8eN3&skey=@crypt_d83b5b90_e4138fcba710f4c7d3da566a64d73f40&lang=zh_CN&pass_ticket=MIHBwaa%252BZqty5E5e1l8UkaAEc48bqCP6Km7WxPAP0txDEdDdWC%252BPE8zfHOXg3ywr
    #       获取消息
    #       获取synckey
    print('start....')
    synckey_list = USER_INIT_DICT['SyncKey']['List']
    sync_list = []
    for item in synckey_list:
        temp = "%s_%s" % (item['Key'], item['Val'],)
        sync_list.append(temp)
    synckey = "|".join(sync_list)

    r1 = requests.get(
        url="https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck",
        params={
            'r': time.time(),
            'skey': TICKET_DICT['skey'],
            'sid': TICKET_DICT['wxsid'],
            'uin': TICKET_DICT['wxuin'],
            'deviceid': "e402310790089148",
            'synckey': synckey
        },
        cookies=ALL_COOKIE_DICT
    )
    if 'retcode:"0",selector:"2"' in r1.text:
        post_dict = {
            'BaseRequest': {
                'DeviceID': "e402310790089148",
                'Sid': TICKET_DICT['wxsid'],
                'Uin': TICKET_DICT['wxuin'],
                'Skey': TICKET_DICT['skey'],
            },
            "SyncKey": USER_INIT_DICT['SyncKey'],
            'rr': 1
        }

        r2 = requests.post(
            url='https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync',
            params={
                'skey': TICKET_DICT['skey'],
                'sid': TICKET_DICT['wxsid'],
                'pass_ticket': TICKET_DICT['pass_ticket'],
                'lang': 'zh_CN'
            },
            json=post_dict
        )
        r2.encoding = 'utf-8'
        msg_dict = json.loads(r2.text)
        for msg_info in msg_dict['AddMsgList']:
            print(msg_info['Content'])

        USER_INIT_DICT['SyncKey'] = msg_dict['SyncKey']

    print(r1.text)
    print('end...')
    return HttpResponse('...')


def hello(request):
    import pymysql
    db = pymysql.connect("192.168.32.101", "root", "redhat", "info")
    cursor = db.cursor()
    cursor.execute("SELECT * from tb_km")
    data_list = cursor.fetchall()
    db.close()

    data_dict = {}
    for data in data_list:
        id, name, times, pic, acc, status, orders = data

        data_dict.update({
            id: {
                'name': name,
                "times": times,
                "pic": pic,
                "acc": acc,
                "status": status,
                "orders": orders
            }

        })

    print(data_dict)
    return render(request, 'base.htm', {'data_dict': data_dict})


def ks_order(request):
    return HttpResponse('OK')
