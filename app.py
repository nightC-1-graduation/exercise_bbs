# splite3をimportする
import sqlite3
# flaskをimportしてflaskを使えるようにする
from flask import Flask , render_template , request , redirect , session , abort , Blueprint , jsonify
# appにFlaskを定義して使えるようにしています。Flask クラスのインスタンスを作って、 app という変数に代入しています。
import datetime
import json
import requests
import sys

dt_now = datetime.datetime.now()

print(dt_now)

print(type(dt_now))
# <class'datetime.datetime'>


app = Flask(__name__)

# Flask では標準で Flask.secret_key を設定すると、sessionを使うことができます。この時、Flask では session の内容を署名付きで Cookie に保存します。
app.secret_key = 'sunabakoza'

@app.route('/')
def index():
    return render_template('index.html')


# GET  /register => 登録画面を表示
# POST /register => 登録処理をする
@app.route('/register',methods=["GET", "POST"])
def register():
    #  登録ページを表示させる
    if request.method == "GET":
        if 'user_id' in session :
            return redirect ('/my_page')
        else:
            return render_template("register.html")
    # ここからPOSTの処理
    else:
        name = request.form.get("name")
        password = request.form.get("password")

        conn = sqlite3.connect('service.db')
        c = conn.cursor()
        c.execute("insert into user values(null,?,?,?,?,?,?,?,?)", (user_name,user_name_kana,address,phone,mail,password,plan))
        conn.commit()
        conn.close()
        return redirect('/login')


# GET  /login => ログイン画面を表示
# POST /login => ログイン処理をする
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if 'user_id' in session :
            return redirect("/my_page")
        else:
            return render_template("login.html")
    else:
        # ブラウザから送られてきたデータを受け取る
        name = request.form.get("user_name")
        password = request.form.get("password")

        # ブラウザから送られてきた name ,password を userテーブルに一致するレコードが
        # 存在するかを判定する。レコードが存在するとuser_idに整数が代入、存在しなければ nullが入る
        conn = sqlite3.connect('service.db')
        c = conn.cursor()
        c.execute("select user_name from users where name = ? and password = ?", (name, password) )
        user_id = c.fetchone()
        conn.close()

        # user_id が NULL(PythonではNone)じゃなければログイン成功
        if user_id is None:
            # ログイン失敗すると、ログイン画面に戻す
            return render_template("login.html")
        else:
            session['user_id'] = user_id[0]
            return redirect("/my_page")


@app.route('/logout')
def logout():
    session.pop('user_id',None)
    # ログアウト後はログインページにリダイレクトさせる
    return redirect("/login")


@app.route('/my_page')
def my_page():
    if 'user_id' in session :
        # クッキーからuser_idを取得
        user_id = session['user_id']
        conn = sqlite3.connect('service.db')
        c = conn.cursor()
        # # DBにアクセスしてログインしているユーザ名と投稿内容を取得する
        # クッキーから取得したuser_idを使用してuserテーブルのnameを取得
        c.execute("select name from user where id = ?", (user_id,))
        # fetchoneはタプル型
        user_info = c.fetchone()
        c.execute("select id,comment,dt_now from bbs where userid = ? and del_flag = 0 order by id", (user_id,))
        comment_list = c.fetchone
        comment_list = []
        for row in c.fetchall():
            comment_list.append({"id": row[0], "comment": row[1], "dt_now": row[2]})

        c.close()
        return render_template('bbs.html' , user_info = user_info , comment_list = comment_list)
    else:
        return redirect("/login")

@app.route('/search', methods=["POST"])
def search():
    conn = sqlite3.connect('service.db')
    c = conn.cursor()
    c.execute("select title from items where title like '%?%'", (user_id,))
    user_info = c.fetchone()
    c.execute("select comment, from items where book_id = ? order by year", (user_id,))
    book_overview = c.fetchone
    book_overview = []
    for row in c.fetchall():
            book_overview.append({"title": row[0], "year": row[1], "comment": row[2]})

@app.route('/add', methods=["POST"])
def add():
    user_id = session['user_id']
    # フォームから入力されたアイテム名の取得
    comment = request.form.get("comment")
    conn = sqlite3.connect('service.db')
    c = conn.cursor()
    # DBにデータを追加する
    c.execute("insert into bbs values(null,?,?,?)", (user_id, comment, dt_now))
    conn.commit()
    conn.close()
    return redirect('/bbs')


@app.route('/edit/<int:id>')
def edit(id):
    if 'user_id' in session :
        conn = sqlite3.connect('service.db')
        c = conn.cursor()
        c.execute("select comment from bbs where id = ?", (id,) )
        comment = c.fetchone()
        conn.close()

        if comment is not None:
            # None に対しては インデクス指定できないので None 判定した後にインデックスを指定
            comment = comment[0]
            # "りんご" ○   ("りんご",) ☓
            # fetchone()で取り出したtupleに 0 を指定することで テキストだけをとりだす
        else:
            return "アイテムがありません" # 指定したIDの name がなければときの対処

        item = { "id":id, "comment":comment }

        return render_template("edit.html", comment=item)
    else:
        return redirect("/login")


# /add ではPOSTを使ったので /edit ではあえてGETを使う
@app.route('/edit' ,methods=["GET"])
def update_item():
    if 'user_id' in session :
        # ブラウザから送られてきたデータを取得
        item_id = request.args.get("item_id") # id
        item_id = int(item_id)# ブラウザから送られてきたのは文字列なので整数に変換する
        comment = request.args.get("comment") # 編集されたテキストを取得する

        # 既にあるデータベースのデータを送られてきたデータに更新
        conn = sqlite3.connect('service.db')
        c = conn.cursor()
        c.execute("update bbs set comment = ? where id = ?",(comment,item_id))
        conn.commit()
        conn.close()

        # アイテム一覧へリダイレクトさせる
        return redirect("/bbs")
    else:
        return redirect("/login")


@app.route('/del' ,methods=["POST"])
def del_task():
    # クッキーから user_id を取得
    id = request.form.get("comment_id")
    id = int(id)
    conn = sqlite3.connect("service.db")
    c = conn.cursor()
    c.execute("update set bbs del_flag = 1 where id = ?", (id,))
    conn.commit()
    c.close()
    return redirect("/my_page")

# これはOK
# @app.route('/bookdb')
# def bookdb():
#     return render_template('bookdb.html')
#
@app.route('/bookdb',methods=["GET", "POST"])
def bookdb():
    if request.method == "GET":
        return render_template('bookdb.html')
    else:
        recieve = sys.stdin.readline()
        print(recieve)
        return "bookdbのGET確認中"
'''
@app.route('/bookdb', methods=["GET", "POST"])
def bookdb():
    if request.method == "GET":
        return render_template("bookdb.html")
    else:
    # フォームから入力されたアイテム名の取得
        bookdata = request.form.get("bookdata")

    # conn = sqlite3.connect('bookshare.db')
    # c = conn.cursor()

    # c.execute("insert into items values(null,?,?,?,?,?,?,?,?,null)", (bookdata[0],bookdata[1],bookdata[2],bookdata[3],bookdata[4],bookdata[5],bookdata[6],bookdata[7]))
    # conn.commit()
    # conn.close()
        return '確認用'
    # redirect('/bookdb')
    '''


    # url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:'
    # # ブラウザから送られてきたISBNデータを受け取る
    # isbn = request.form.get("isbn")
    # req_url = url + isbn
    # res = requests.get(req_url)
    # return '登録できないよ'
    # # response.text
    # WebAPIのURLに引数文字列を追加
    # url = 'https://www.googleapis.com/books/v1/volumes?q=isbn:' + '9784893096609'
    # WebAPIの呼び出し
    # res = requests.get('https://www.googleapis.com/books/v1/volumes?q=isbn:9784893096609')

    # title = res.items[0].volumeInfo.title
    # author = res.items[0].volumeInfo.authors[0]
    # year = res.items[0].volumeInfo.publishedDate
    # synopsis = res.items[0].volumeInfo.description
    # book_photo = res.items[0].volumeInfo.imageLinks.smallThumbnail
    # pages = res.items[0].volumeInfo.pageCount
    # isbn = res.items[0].volumeInfo.industryIdentifiers[1].identifier
    # genre = res.items[0].volumeInfo.categories

    # DBにデータを追加する
    # conn = sqlite3.connect('bookshare.db')
    # c = conn.cursor()
    # c.execute("insert into items values(null,?,?,?,?,?,?,?,?)", (title, author, year, synopsis, isbn, book_photo, genre, pages, ) )
    # conn.commit()
    # conn.close()
    # return '登録できないよ'


# 図書検索機能まだできてないよ
# # GET  /search => 検索画面を表示
# # POST /search => 検索処理をする
# @app.route("/titlesearch", methods=["POST"])
# def search():
#     # ブラウザから送られてきた検索キーワードを受け取る
#     name = request.form.get("keyword")

#     # ブラウザから送られてきた keywordと itemsテーブルに一致するレコードが
#     # 存在するかを判定する。レコードが存在したら
#     # 本の情報を表示させたい
#     conn = sqlite3.connect('bookshare.db')
#     c = conn.cursor()
#     # 検索キーワードが本のタイトルと部分一致したらカラム全部取り出してみる
#     c.execute("select * from items where title like ?", ('%'+keyword+'%',) )

#     # この下からはまだ
#     # 

#     user_id = c.fetchall()
#     conn.close()
#     # # DBから取得してきたuser_id、ここの時点ではタプル型
#     # print(type(user_id))
#     # # user_id が NULL(PythonではNone)じゃなければログイン成功
#     # if user_id is None:
    #     # ログイン失敗すると、ログイン画面に戻す
    #     return render_template("login.html")
    # else:
    #     session['user_id'] = user_id[0]
    #     return redirect("/bbs")


@app.errorhandler(403)
def mistake403(code):
    return 'There is a mistake in your url!'


@app.errorhandler(404)
def notfound404(code):
    return "404だよ！！見つからないよ！！！"


# __name__ というのは、自動的に定義される変数で、現在のファイル(モジュール)名が入ります。 ファイルをスクリプトとして直接実行した場合、 __name__ は __main__ になります。
if __name__ == "__main__":
    # Flask が持っている開発用サーバーを、実行します。
    app.run(debug = True)