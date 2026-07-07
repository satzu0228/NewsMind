import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "newsmind.db"


def u(text: str) -> str:
    return text.encode("ascii").decode("unicode_escape")


ARTICLES = [
    (
        u(r"\u79d1\u6280"),
        "Artificial intelligence is being used in newsroom editing, hospital services and smart manufacturing at the same time\u3002"
        "Several companies have released tools for content classification, information extraction and automatic summarization\u3002"
        "Engineers said that model accuracy is only one part of deployment, because stable response time and reliable feedback loops are also required\u3002"
        "In recent pilot projects, long articles can be processed within seconds and then sent to different business modules according to topic labels\u3002"
        "Experts also warned that generated content still needs human review when it is used in public communication\u3002"
        "Future systems will focus on lightweight models, industry data and continuous evaluation from real users\u3002",
    ),
    (
        u(r"\u6559\u80b2"),
        "Several universities have announced curriculum reform plans that add artificial intelligence, data analysis and project based learning\u3002"
        "The new courses require students to understand both technical methods and the practical limits of automated tools\u3002"
        "Some schools have built experimental platforms where students can test news classification, summary generation and public opinion analysis\u3002"
        "Teachers believe that technology classes should not only follow popular trends, but should also train data ethics and independent judgment\u3002"
        "To reduce pressure, course projects are divided into stages with process evaluation and team presentations\u3002"
        "More universities plan to cooperate with companies and research institutes so that students can work with real datasets\u3002",
    ),
    (
        u(r"\u793e\u4f1a"),
        "A new public service platform has been launched to help residents check social insurance, book medical appointments and consult government services\u3002"
        "The platform connects several department databases and uses an intelligent question answering module to recommend the correct service entrance\u3002"
        "On the first day, traffic increased quickly, and the most popular functions were medical services, transportation information and community activities\u3002"
        "Community workers said that online processing reduced waiting time, while offline counters are still kept for elderly residents\u3002"
        "Volunteers will also provide guidance for users who are not familiar with mobile applications\u3002"
        "The city plans to improve privacy protection, voice guidance and progress reminders based on user feedback\u3002",
    ),
    (
        u(r"\u8d22\u7ecf"),
        "Many cities have released policies to encourage consumption in electric vehicles, home appliances, tourism and neighborhood retail\u3002"
        "Market analysts said that service consumption is recovering as travel demand improves and online platforms connect with physical stores\u3002"
        "Some shopping districts use coupons, night markets and better traffic planning to increase restaurant and retail orders\u3002"
        "Businesses are also using digital membership systems to understand customer preferences and improve inventory turnover\u3002"
        "Experts noted that short term subsidies should be combined with better product quality and stronger income expectations\u3002"
        "Financial institutions will continue to support small merchants with credit services and cash flow tools\u3002",
    ),
    (
        u(r"\u4f53\u80b2"),
        "The national youth football invitational tournament ended over the weekend with several school teams showing strong technique and teamwork\u3002"
        "The event included group matches, knockout rounds and skill demonstrations for players from different regions\u3002"
        "Coaches said that youth football training should focus on basic movement, tactical understanding and mental strength rather than only scores\u3002"
        "Several players said that continuous matches helped them understand the importance of physical preparation and communication\u3002"
        "The organizers introduced video replay and data records for passing accuracy, running distance and shooting efficiency\u3002"
        "Sports experts believe that school competitions can discover young talent and encourage more students to join regular exercise\u3002",
    ),
]


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        inserted = 0
        for category, content in ARTICLES:
            exists = cur.execute(
                "SELECT id FROM news WHERE content = ? LIMIT 1",
                (content,),
            ).fetchone()
            if exists:
                continue
            cur.execute(
                """
                INSERT INTO news (category, content, tokenized, length, token_length, created_at)
                VALUES (?, ?, NULL, ?, 0, datetime('now', 'localtime'))
                """,
                (category, content, len(content)),
            )
            inserted += 1
        conn.commit()
        total = cur.execute("SELECT COUNT(*) FROM news").fetchone()[0]
        print(f"inserted={inserted}, total={total}, db={DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
