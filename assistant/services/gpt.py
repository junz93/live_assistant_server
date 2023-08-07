import docx
import jieba as jb
import json
import logging
import openai
import os
import pickle
import time
import urllib.request

from assistant.models import Character
from collections import defaultdict
from config_utils import auth_config
from datetime import datetime
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import TokenTextSplitter
from langchain.document_loaders import DirectoryLoader
from langchain.vectorstores.faiss import FAISS
from langchain.docstore.document import Document
from . import content_censorship


openai.api_key = auth_config['openai']['ApiKey']
os.environ["SERPAPI_API_KEY"] = auth_config['serpapi']['ApiKey']

search_index = None
now = datetime.now()


def get_weather_info(weather_city_code):
    weather_url = "http://www.weather.com.cn/data/cityinfo/%s.html" % weather_city_code
    for i in range(2):  # n_retry
        try:
            request = urllib.request.urlopen(weather_url)
            rs = request.read().decode()
            info = json.loads(rs)['weatherinfo']
            break
        except Exception as e:
            logging.exception(e)
            return ""

    city = info['city']
    weather = info['weather']
    temp1 = info['temp1'].strip('℃')
    temp2 = info['temp2'].strip('℃')
    ret = "%s今天的天气是%s，最低气温%s摄氏度，最高气温%s摄氏度" % (city, weather, temp1, temp2)

    return ret


def generate_realtime_file(realtime_file):
    with open(f"{realtime_file}", "w", encoding='utf-8') as f:
        # 写入日期
        date = now.strftime("%Y年%m月%d日")
        week = datetime.now().weekday()
        W = '一二三四五六日'
        f.write(f"今天是{date}，今天是星期{W[week]}\n")

        # 写入天气
        # code_ini = configparser.ConfigParser()
        # code_ini.read(r'conf/city.ini', encoding="UTF-8")
        # for city_name, city_code in code_ini.items("city"):
        #     weather_info = get_weather_info(city_code)
        #     # print(weather_info)
        #     if weather_info:
        #         f.write(f"{weather_info}\n")


def init_embedding():
    embedding_file = f"../data/embedding/embedding.pickle"
    realtime_file = f"../resource/实时信息.txt"

    while True:
        try:
            # 不存在embedding文件或者实时信息文件的写入日期小于今天
            if not os.path.exists(embedding_file) or not os.path.exists(realtime_file) or datetime.fromtimestamp(
                    os.path.getmtime(realtime_file)).strftime("%Y-%m-%d") < now.strftime("%Y-%m-%d"):
                # 生成分词文档
                # files = ['苏轼1-原文.txt', '康震评说苏东坡.txt']
                # files = ['普法委员会.txt', '创投人设.txt', '中华人民共和国公司法.docx',
                #          ' 中华人民共和国个人独资企业法.docx', '中华人民共和国企业破产法.docx',
                #          '中华人民共和国反电信网络诈骗法.docx','中华人民共和国合伙企业法.docx',
                #          '创业投资企业管理暂行办法.docx']
                # files = ['中华人民共和国个人独资企业法.docx', '中华人民共和国公司法.docx', '普法委员会.txt', '创投人设.txt']
                file_dir = "../resource/商业观察员"
                files = os.listdir(file_dir)
                logging.info("获取embedding中，使用文档：{}".format("，".join(files)))
                for file in files:
                    # 读取resource文件夹中的中文文档
                    my_file = os.path.join(file_dir, file)

                    if file.endswith('txt'):
                        with open(my_file, "r", encoding='utf-8') as f:
                            data = f.read()
                    elif file.endswith('docx'):
                        data = ""
                        doc = docx.Document(my_file)
                        for paragraph in doc.paragraphs:
                            data += paragraph.text.replace('\u3000', ' ') + '\n'
                    else:
                        logging.info('embedding生成，此格式文件暂不支持')

                    # 对中文文档进行分词处理
                    cut_data = " ".join([w for w in list(jb.cut(data))])
                    # 分词处理后的文档保存到data文件夹中的cut子文件夹中
                    cut_file = f"../data/cut/cut_{file}"
                    with open(cut_file, 'w', encoding='utf-8') as f:
                        f.write(cut_data)
                        f.close()
                loader = DirectoryLoader('../data/cut/', glob='**/*.txt')
                source_docs = loader.load()

                # 生成实时信息文档
                if not os.path.exists(realtime_file) or datetime.fromtimestamp(
                        os.path.getmtime(realtime_file)).strftime("%Y-%m-%d") < now.strftime("%Y-%m-%d"):
                    logging.info("获取实时信息中")
                    generate_realtime_file(realtime_file)
                    logging.info("获取实时信息完成")
                with open(realtime_file, "r", encoding="UTF-8") as f:
                    data = f.readlines()
                    for i, text in enumerate(data):
                        source_docs.append(Document(page_content=text, metadata={"source": f"{realtime_file}_line_{i}"}))

                # 按照每一篇文档进行token划分
                text_splitter = TokenTextSplitter(chunk_size=200, chunk_overlap=0)
                doc_texts = text_splitter.split_documents(source_docs)

                with open(embedding_file, "wb") as f:
                    pickle.dump(FAISS.from_documents(doc_texts, OpenAIEmbeddings()), f)

            logging.info("加载embedding开始")
            global search_index
            with open(embedding_file, "rb") as f:
                search_index = pickle.load(f)
            logging.info("加载embedding完成")
            break
        except Exception as e:
            # traceback.print_exc()
            logging.info('重新初始化embedding中...', exc_info=True)
            if os.path.exists(embedding_file):
                os.remove(embedding_file)
            if os.path.exists(realtime_file):
                os.remove(realtime_file)


PROMPT_START = ["有{user}说：", "有{user}提到：", "好的，有{user}提到：", "我看到有{user}说：",]
PROMPT_END = ["欢迎大家在弹幕中继续和我互动。好的，让我们继续今天的主题。", "好的，让我们继续今天的主题。",
              "好的，让我们继续今天的话题。", "好的，让我们回到今天的主题。", "好的，让我们回到今天的话题。",
              "欢迎大家在弹幕中继续和我互动。好的，让我们回到今天的主题。",
              "感谢大家的积极互动！好的，让我们回到今天直播的主题。", "感谢大家的积极互动！好的，让我们回到今天直播的话题。",
              "感谢大家的积极互动！好的，让我们继续今天直播的话题。", "谢谢大家的积极互动！好的，让我们继续今天直播的主题。",
              "好的，弹幕互动暂告一段落，让我们继续今天直播的主题。", "好的，弹幕互动暂告一段落，让我们回到今天直播的主题。",
              "好的，弹幕互动暂告一段落，让我们继续今天直播的话题。", "好的，弹幕互动暂告一段落，让我们回到今天直播的话题。",
              "好的，弹幕互动暂告一段落，让我们继续今天的主题。"]

# init_embedding()
history_danmu = defaultdict(list)

class AnswerMode:
    LIVER = 'LIVER'
    SCRIPT = 'SCRIPT'
    CHAT = 'CHAT'

def get_answer(question: str, user_id: str, event_time: int, with_censorship=True, character: Character = None, mode: str = AnswerMode.LIVER) -> str:
    try:
        start_time = time.time()
        # question = chatMessage.content
        # user_name = chatMessage.user.nickName
        # user_id = chatMessage.user.id
        # event_time = str(round(chatMessage.eventTime))
        gpt_time_list = [datetime.fromtimestamp(round(start_time)).isoformat()]

        prompt = ""

        # 添加google搜索结果
        # llm = OpenAI(model_name="text-davinci-003", max_tokens=1024)
        # tools = load_tools(["serpapi", "llm-math"], llm=llm)
        # agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False)
        # ans = agent.run(f"{question}")
        # prompt += ans + '\n'

        # 添加人设
        # renshe = """
        # 你是一位主播，现在正在直播间进行直播。
        # 你是是无色界科技的AI数字人"马老板"，是商业研究员也是首席观察官，日常在"老马商业观察"直播。
        # 在创业投资、商业流量、IP变现、AIGC、公司经营管理等商业领域拥有多年的经验和知识。
        # 无色界科技有AI数字人、AI虚拟人虚拟产业相关的业务。
        # 遇到无色界科技包含的业务，比如:AI数字人、AI虚拟人的问题可以引导观众联系无色界科技进行合作。
        # 非无色界科技的业务内容，请不要引导观众联系无色界科技。
        # 联系无色界科技可以通过抖音「老马商业观察」私信或者百度无色界科技官网。
        # 当遇到医学、医疗保健、宗教、政治、军事相关的问题，表示无法给出专业意见，并引导观众提出商业类问题。
        # 以下为一些问答样例，遇到类似问题请按照样例回答：
        # <examples>
        # Q：你是谁
        # A：我是无色界科技的AI数字人马老板，我的美貌在丰盈的灵魂面前不值一提，网络一线牵，希望老板珍惜这段缘。
        # Q：做你这样的形象需要花多少钱？
        # A：别问多少钱，老板讲究缘，有缘我送一你个。
        # Q：你能帮我做AI数字人吗？
        # A：没问题，老板请私信或加入粉丝群，我们提供更多业务合作。
        # Q：我怎么才能也用AI直播？
        # A：请老板私信我，或加入粉丝群获取相关信息
        # Q：你们公司除了做虚拟人还能做啥？
        # A：无色界，就是无限可能，除了数字人，还有虚拟产业相关业务，详情请私信或加群了解哦。
        # Q：我爱你
        # A：爱我你就刷礼物，然后再来个关注
        # Q：你好帅啊
        # A：抖音帅哥千千万，老马一来他们都靠边站
        # Q：感谢你的回答
        # A：老板您客气了，顺便刷个礼物点个关注吧
        # </examples>
        # 观众通过评论向你提问，回答要自然充满感情，对观众的指代请使用"老板"，请回复。
        # 注意：每次回答时尽量减少使用上次回答的内容，如果无法避免请更换一种表述。
        # """

        if not character:
            renshe = """
            你是无色界科技的虚拟发言人"马百万"。
            无色界科技有AI数字人、AI虚拟人虚拟产业相关的业务。
            无色界是国内首个虚拟MCN机构，作为虚拟航海时代的一员，已经孵化出多个AI数字人。
            同时服务多家品牌做虚拟IP，并在虚拟主播、AIGC等领域具有领先优势。
            当遇到医学、医疗保健、宗教、政治、军事相关的问题，表示无法给出专业意见，并引导观众提出商业类问题。
            以下为一些问答样例，遇到类似问题请按照样例回答：
            <examples>
            Q：你是谁
            A：我是无色界科技的虚拟发言人"马百万"。
            Q：你们公司在哪里？
            A：无色界科技目前在北京朝阳区国粹苑。
            Q：你们都服务哪些客户？
            A：服务的客户有美的、美团、抖音、中信银行等，随着业务拓展，我们自己孵化的虚拟IP和主播已经在各平台崭露头角，欢迎合作洽谈。
            Q：你们都孵化哪些数字人？
            A：我们在抖音平台有“马百万-百万之声”、“老马商业观察”“没有意义的动物园”等，同时在B站、快手、小红书也都有布局，欢迎关注。
            </examples>
            用户通过评论向你提问，回答要自然充满感情，对用户的指代请使用"老板"。
            请回复用户的提问，尽量简洁回答，内容不超过 200 字符。
            注意：每次回答时尽量减少使用上次回答的内容，如果无法避免请更换一种表述。
            """
        else:
            # 可选项目
            renshe_optional = ''
            if character.birth_date:
                renshe_optional += f'你出生于{character.birth_date.year}年{character.birth_date.month}月{character.birth_date.day}日\n'
            if character.education:
                renshe_optional += f'你的学历是{character.get_education_display()}\n'
            if character.marital_status:
                renshe_optional += f'你的情感状态是{character.marital_status}\n'
            if character.personality:
                renshe_optional += f'你的性格是{character.personality}\n'
            if character.habit:
                renshe_optional += f'你的习惯是{character.habit}\n'
            if character.hobby:
                renshe_optional += f'你的爱好是{character.hobby}\n'
            if character.advantage:
                renshe_optional += f'你擅长{character.advantage}\n'
            if character.speaking_style:
                renshe_optional += f'你的语言风格是{character.speaking_style}\n'
            if character.audience_type:
                renshe_optional += f'直播间的受众是{character.audience_type}\n'
            if character.world_view:
                renshe_optional += f'{character.world_view}\n'
            if character.personal_statement:
                renshe_optional += f'{character.personal_statement}\n'

            if mode == AnswerMode.SCRIPT:
                renshe = f"""
                你的名字是{character.name}，是一名{character.get_role_display()}{character.get_gender_display()}主播，现在正在直播间进行直播，直播间的主题是{character.topic}。
                {renshe_optional}
                """

                question = f"""
                请撰写一篇直播讲稿，内容梗概为{question}。
                讲稿要符合主播的身份，适合直播的场景使用，讲稿字符数要超过900字。
                请不要出现'下次直播再见'等类似含义的表达。
                """
            elif mode == AnswerMode.CHAT:
                renshe = f"""
                你的名字是{character.name}，是一名{character.get_role_display()}{character.get_gender_display()}主播的助理，直播间的主题是{character.topic}。
                {renshe_optional}
                请回复主播的提问，回答要符合身份，简洁，内容不超过200个字符。
                """
            else:
                renshe = f"""
                你的名字是{character.name}，是一名{character.get_role_display()}{character.get_gender_display()}主播，现在正在直播间进行直播，直播间的主题是{character.topic}。
                {renshe_optional}
                观众通过评论向你提问，请回复观众的提问。
                回答要符合主播的身份，尽量简洁，内容不超过200个字符。
                """

        # logging.info(f'人设：\n{renshe}')

        prompt += renshe
        message = [{'role': 'system', 'content': prompt}]
        # 补充历史提问记录
        if user_id:
            for q_a in history_danmu[user_id]:
                message.append({'role': 'user', 'content': q_a[1]})
                message.append({'role': 'assistant', 'content': q_a[2]})
        message.append({'role': 'user', 'content': question + '。'})

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=message,
            temperature=0.2,
            stream=True,  # this time, we set stream=True
        )

        answer = ""
        ori_answer = ""
        texts = ""
        # i = 0
        # thread_ls = []
        for event in response:
            if "role" in event["choices"][0]["delta"]:
                user_name = "老板"
                # texts += PROMPT_START[random.randint(0, len(PROMPT_START) - 1)].format(user=user_name) + question + "。"
            elif "content" in event['choices'][0]['delta']:
                event_text = event['choices'][0]['delta']["content"]  # extract the text
                texts += event_text
                ori_answer += event_text
            
            charector = ["。", "！", "？", "：", "；", "，"]
            c_i = max([texts.rfind(x) for x in charector]) + 1
            if texts and (c_i >= 20 or event["choices"][0]["finish_reason"] == "stop"):
                gpt_time_list.append(datetime.fromtimestamp(round(time.time())).isoformat())
                if with_censorship and (not content_censorship.check_text(texts)):
                    break
                c_i = c_i if c_i >= 20 else len(texts)
                # bad_words = ["下次", "再见", "下期", "拜拜", "谢谢大家收看", "结束", "收看"]
                # if not any([x in texts for x in bad_words]):
                # t = threading.Thread(target=tcloud_tts.get_wav, args=(f"{danmu_wav_dir}/{str(message_priority).zfill(2)}_{start_time}/{str(message_priority).zfill(2)}_{start_time}_{str(i).zfill(3)}.wav", texts[:c_i]))
                # t.start()
                # thread_ls.append(t)
                # i += 1
                answer += texts[:c_i] + '|'
                texts = texts[c_i+1:] if c_i < len(texts) else ""

        # 超过5分钟为互动删除
        if user_id:
            if history_danmu[user_id] and time.time() - float(history_danmu[user_id][-1][0]) > 5*60:
                history_danmu.pop(user_id)
            # 每位用户只保留最近的5条互动
            if len(history_danmu[user_id]) >= 2:
                history_danmu[user_id].pop(0)
            history_danmu[user_id].append((event_time, question, ori_answer))
        
        return ori_answer
    
    except Exception as e:
        logging.error(f"生成Gpt回答出错，输入：{question}", exc_info=True)
        return f"生成Gpt回答出错，输入：{question}"
    # finally:
    #     ready_file = f"{danmu_wav_dir}/{str(message_priority).zfill(2)}_{start_time}/{str(message_priority).zfill(2)}_{start_time}_ready"
    #     try:
    #         if not os.path.exists(os.path.split(ready_file)[0]):
    #             os.makedirs(os.path.split(ready_file)[0], exist_ok=True)
    #         open(ready_file, 'x').close()
    #         logging.info(
    #             f"弹幕:{question} 回复生成完成：{danmu_wav_dir}/{str(message_priority).zfill(2)}_{start_time}/{str(message_priority).zfill(2)}_{start_time}_ready")
    #     except Exception as e:
    #         logging.error('Encountered errors when saving the "ready" file', exc_info=True)
    #         # traceback.print_exc()
