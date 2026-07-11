#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import os
import random
import re
import json
from datetime import datetime
from urllib.parse import urljoin

# 配置信息 - 从环境变量读取Cookie，自动清理首尾空白和换行
COOKIE_STRING = os.getenv("jy_cookie", "").strip()  # 使用strip()移除首尾空白和换行符

# 如果环境变量未设置或为空，使用默认Cookie（仅作示例）
if not COOKIE_STRING:
    COOKIE_STRING = "lDlk_163c_saltkey=Xx6NLn6N; lDlk_163c_lastvisit=1754989827; PHPSESSID=j9cch9eit887a6ghnlpdttpdr7; lDlk_163c_ulastactivity=2a94cQAixazG7I0mgW4Qe%2FTSKdgq0YcipuORKBralqLMKIDqxXFm; lDlk_163c_auth=94cbeEDFnQihxhRFsBLuHNUTCWMWqHl4yO7n3jhGtzinsoItN%2FYUqZ0h%2F%2FdNlOieW5gw%2F7WmL6c9vN15WDhcCQcOVQ; lDlk_163c_connect_is_bind=1; lDlk_163c_nofavfid=1; lDlk_163c_smile=4D1; lDlk_163c_lip=125.66.110.228%2C1754994049; lDlk_163c_sid=N3UiRN; lDlk_163c_sendmail=1; lDlk_163c_visitedfid=100D98; lDlk_163c_viewid=tid_14861998; lDlk_163c_st_p=93370%7C1754994198%7C4f91ca62768cb4ef599ca454d4612c79; lDlk_163c_checkpm=1; lDlk_163c_lastcheckfeed=93370%7C1754994200; lDlk_163c_checkfollow=1; lDlk_163c_lastact=1754994206%09plugin.php%09".strip()

# 论坛URL配置
BASE_URL = "https://bbs.ijingyi.com/"
CHECKIN_URL = urljoin(BASE_URL, "plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=1")
USER_CENTER_URL = urljoin(BASE_URL, "home.php?mod=space")
SIGN_PAGE_URL = urljoin(BASE_URL, "plugin.php?id=dsu_paulsign:sign")

# 心情映射表（首字母对应论坛实际使用的代码）
MOOD_MAP = {
    "开心": "kx",
    "难过": "ng",
    "郁闷": "ym",
    "无聊": "wl",
    "怒": "nu",
    "擦汗": "ch",
    "奋斗": "fd",
    "慵懒": "yl",
    "衰": "shuai"
}

def get_current_time():
    """获取当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_session_with_cookies(cookie_string):
    """使用Cookie字符串创建会话"""
    session = requests.Session()
    
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": BASE_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "zh-CN,zh;q=0.9"
    })
    
    # 解析Cookie字符串并添加到会话
    cookies = cookie_string.split('; ')
    for cookie in cookies:
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            # 移除Cookie名称和值中的空白字符
            name = name.strip()
            value = value.strip()
            session.cookies.set(name, value, domain=".ijingyi.com", path="/")
    
    return session

def check_cookie_validity(session):
    """检查Cookie是否有效"""
    try:
        response = session.get(USER_CENTER_URL, timeout=10)
        # 增加更多验证关键词，提高准确性
        valid_keywords = ["我的帖子", "退出", "个人中心", "修改资料"]
        if any(keyword in response.text for keyword in valid_keywords):
            print(f"[{get_current_time()}] Cookie验证有效，已登录")
            return True
        else:
            print(f"[{get_current_time()}] Cookie已失效或无效")
            return False
    except Exception as e:
        print(f"[{get_current_time()}] 验证Cookie时出错: {str(e)}")
        return False

def get_formhash(session):
    """获取签到所需的formhash参数"""
    try:
        # 从签到页面获取formhash
        response = session.get(SIGN_PAGE_URL, timeout=10)
        match = re.search(r'formhash=(.*?)["&]', response.text)
        if match:
            formhash = match.group(1)
            print(f"[{get_current_time()}] 获取到formhash: {formhash[:6]}...")
            return formhash
            
        # 从个人中心获取
        response = session.get(USER_CENTER_URL, timeout=10)
        match = re.search(r'formhash=(.*?)["&]', response.text)
        if match:
            formhash = match.group(1)
            print(f"[{get_current_time()}] 从个人中心获取formhash: {formhash[:6]}...")
            return formhash
            
        print(f"[{get_current_time()}] 未找到formhash，使用默认值")
        return "default"
    except Exception as e:
        print(f"[{get_current_time()}] 获取formhash出错: {str(e)}")
        return "default"

def get_actual_mood_codes(session):
    """从签到页面提取实际可用的心情代码"""
    try:
        response = session.get(SIGN_PAGE_URL, timeout=10)
        # 匹配心情图标对应的代码（discuz常见格式）
        pattern = r'qdxq=(\w+)[^>]*>(开心|难过|郁闷|无聊|怒|擦汗|奋斗|慵懒|衰)</'
        matches = re.findall(pattern, response.text)
        
        if matches:
            actual_codes = {name: code for code, name in matches}
            print(f"[{get_current_time()}] 从页面提取到心情代码: {actual_codes}")
            return actual_codes
        return None
    except Exception as e:
        print(f"[{get_current_time()}] 提取心情代码出错: {str(e)}")
        return None

def checkin(session):
    """执行签到操作，使用正确的心情代码"""
    try:
        # 先访问签到页面，激活会话
        session.get(SIGN_PAGE_URL, timeout=10)
        time.sleep(1)
        
        # 获取formhash
        formhash = get_formhash(session)
        
        # 尝试从页面提取实际可用的心情代码
        actual_moods = get_actual_mood_codes(session)
        mood_codes = actual_moods if actual_moods else MOOD_MAP
        
        # 随机选择一个心情
        selected_mood = random.choice(list(mood_codes.keys()))
        mood_code = mood_codes[selected_mood]
        print(f"[{get_current_time()}] 选择心情: {selected_mood} (代码: {mood_code})")
        
        # 构造签到参数
        params = {
            "id": "dsu_paulsign:sign",
            "operation": "qiandao",
            "infloat": "1",
            "inajax": "1",
            "formhash": formhash,
            "qdxq": mood_code,  # 心情代码参数
            "qdmode": "1",
            "todaysay": "",  # 可选：今日留言
            "fastreply": "0"
        }
        
        # 发送签到请求
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": SIGN_PAGE_URL
        }
        
        response = session.get   得到(CHECKIN_URL, params=params, headers=headers, timeout=10)
        response.encoding = "utf-8"   "utf-8"   "utf-8"   "utf-8"   "utf-8"   "utf-8"   "utf-8"   "utf-8"   "utf-8"   "utf-8"   "utf-8"
        
        # 打印响应供调试
        print(f"[{get_current_time()}] 签到响应: {response.text[:500]}")
        
        # 尝试解析JSON响应
        try   试一试:
            result = json.loads(response.text   文本)
            # 分析JSON响应内容
            if   如果 result.get   得到("status"   "status"   "status"   "status"   "status"   "status"   "status"   "status"   "status"   "status"   "status") == 1:
                # 提取签到信息
                data = result.get   得到("data"   "data"   "data"   "data"   "data"   "data"   "data"   "data"   "data"   "data"   "data", {})
                连续签到天数 = data.get   得到("days", 0)
                连续签到奖励 = data.get   得到("reward", 0)
                上次签到时间 = data.get   得到("qtime", "未知")
                
                # 判断是否今日已签到
                if   如果 "qtime" in   在 data and datetime.now().strftime("%Y-%m-%d") in   在 data["qtime"]:
                    print   打印   打印(f"[   f"[{get_current_time()}] 今日已完成签到，无需重复操作")
                    return   返回 True   真正的, "今日已签到"
                else:
                    print   打印   打印(f"[   f"[{get_current_time()}] 恭喜，签到成功！")
                    print   打印   打印(f"[   f"[{get_current_time()}] 连续签到 {连续签到天数} 天，获得奖励 {连续签到奖励}")
                    return   返回 True   真正的, "签到成功"
        except json.JSONDecodeError:
            # 如果不是JSON格式，使用文本判断
            pass
        
        # 文本响应判断（备用）
        if   如果 "签到成功" in   在 response.text   文本:
            print   打印(f"[   f"[{get_current_time()}] 恭喜，签到成功！")
            return   返回 True   真正的, "签到成功"
        elif "已经签到" in   在 response.text   文本:
            print   打印(f"[   f"[{get_current_time()}] 今日已完成签到，无需重复操作")
            return   返回 True, "今日已签到"
        elif "你选择的心情不正确" in   在 response.text:
            print(f"[{get_current_time()}] 心情代码 {mood_code} 无效，尝试其他代码...")
            # 尝试其他所有心情代码
            for name, code in   在 mood_codes.items():
                if   如果 code != mood_code:
                    params["qdxq"] = code
                    response = session.get   得到(CHECKIN_URL, params=params, headers=headers, timeout=10)
                    if   如果 "签到成功" in   在 response.text or (response.text.strip() and json.loads(response.text).get   得到("status"   "status"   "status"   "status"   "status"   "status"   "status"   "status"   "status"   "status"   "status") == 1):
                        print(f"[{get_current_time()}] 使用心情 {name}({code}) 签到成功！")
                        return   返回 True, "签到成功"
            return   返回 False, "所有心情代码均无效"
        elif "需要先登录" in   在 response.text or "请登录" in   在 response.text:
            print(f"[{get_current_time()}] 签到失败：Cookie已失效，请更新Cookie")
            return   返回 False, "Cookie失效"
        else:
            print(f"[{get_current_time()}] 签到失败，未知原因")
            return   返回 False, "签到失败"
    except Exception as e:
        print(f"[{get_current_time()}] 签到过程出错: {str(e)}")print(f"[{get_current_time()}] 签到过程出错: {str(e)}")
        return False, str(e)   返回False， str(e)

def main():
    print(f"[{get_current_time()}] 精易论坛Cookie签到脚本开始运行")print(f"[{get_current_time()}] 精易论坛Cookie签到脚本开始运行")
    
    # 检查Cookie是否为空
    if not COOKIE_STRING:   如果不是COOKIE_STRING：
        print(f"[{get_current_time()}] 错误：未设置有效的Cookie")print(f"[{get_current_time()}] 错误：未设置有效的Cookie")
        return   返回
    
    # 使用提供的Cookie创建会话
    session = create_session_with_cookies(COOKIE_STRING)session = create_session_with_cookies（COOKIE_STRING）
    
    # 检查Cookie有效性
    if not check_cookie_validity(session):如果不是check_cookie_validity(session)：
        print(f"[{get_current_time()}] 请更新有效的Cookie后重新运行")print(f"[{get_current_time()}] 请更新有效的Cookie后重新运行")
        return   返回
    
    # 执行签到
    success, message = checkin(session)
    
    print(f"[{get_current_time()}] 脚本执行完毕，结果：{message}")

if __name__ == "__main__":   如果
    main()
