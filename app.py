import os, sys, subprocess, tempfile
from flask import Flask, render_template, request, abort
from data import SUBJECTS, PY_EXERCISES, get_lessons_by_subject, get_hsg_exercises

app = Flask(__name__)
SUBJECT_MAP = {s['id']: s for s in SUBJECTS}

def run_python_code(code, stdin_data, timeout=5):
    fd, path = tempfile.mkstemp(suffix='.py', text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f: f.write(code)
        res = subprocess.run([sys.executable, path], input=stdin_data, capture_output=True, text=True, timeout=timeout)
        return res.stdout.strip(), res.stderr.strip(), res.returncode
    except subprocess.TimeoutExpired: return '', 'Lỗi: Timeout', -1
    finally:
        try: os.unlink(path)
        except: pass

@app.route('/')
def index(): return render_template('index.html', subjects=SUBJECTS)

@app.route('/study')
def all_study():
    lessons = get_lessons_by_subject('all')
    return render_template('study.html', subject={'name': 'Tất cả môn học'}, lessons=lessons)

@app.route('/study/<subject_id>')
def study(subject_id):
    subj = SUBJECT_MAP.get(subject_id)
    if not subj: abort(404)
    lessons = get_lessons_by_subject(subject_id)
    return render_template('study.html', subject=subj, lessons=lessons)

@app.route('/hsg', methods=['GET', 'POST'])
def hsg():
    exercises = get_hsg_exercises() 
    ex_id = request.args.get('id', 0)
    try: ex = exercises[int(ex_id)]
    except: ex = exercises[0] if exercises else None
    
    show_sol, user_ans = False, ""
    if request.method == 'POST':
        user_ans, show_sol = request.form.get('answer', ''), True
    return render_template('hsg.html', exercises=exercises, current=int(ex_id), exercise=ex, show_solution=show_sol, user_answer=user_ans)

@app.route('/tin', methods=['GET', 'POST'])
def tin():
    ex_id = request.args.get('ex') or next(iter(PY_EXERCISES))
    code = PY_EXERCISES[ex_id]['starter']; results, summary = None, None
    if request.method == 'POST':
        ex_id = request.form.get('exercise_id', ex_id)
        code = request.form.get('code', '')
        ex = PY_EXERCISES[ex_id]
        results, passed = [], 0
        for idx, tc in enumerate(ex['test_cases'], 1):
            out, err, rc = run_python_code(code, tc['input'])
            ok = (rc == 0 and out.strip() == tc['expected'].strip())
            if ok: passed += 1
            results.append({'index': idx, 'input': tc['input'], 'expected': tc['expected'], 'got': out if rc == 0 else err, 'passed': ok})
        summary = {'passed': passed, 'total': len(ex['test_cases'])}
    return render_template('tin.html', exercises=PY_EXERCISES, current=ex_id, code=code, results=results, summary=summary)
# --- CỬA HẬU ADMIN (Đường link bí mật) ---
ADMIN_SECRET_KEY = "admin123" # Bạn có thể đổi mật khẩu tại đây

@app.route('/quantri-bimat')
def admin_dashboard():
    # Kiểm tra xem trên link có ?key=admin123 không
    if request.args.get('key') != ADMIN_SECRET_KEY:
        return "<h2 style='text-align:center; margin-top:50px; color:red;'>Lỗi 403: Bạn không có quyền truy cập trang này!</h2>", 403
    
    # Thống kê số lượng bài học hiện có
    thuong = get_lessons_by_subject('all')
    hsg = get_hsg_exercises()
    return render_template('admin.html', total_thuong=len(thuong), total_hsg=len(hsg))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 9000))
    app.run(host='0.0.0.0', port=port)