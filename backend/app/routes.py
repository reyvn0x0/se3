from flask import Blueprint, render_template
from app.models import DegreeProgram
from app import db

main = Blueprint('main', __name__)

@main.route("/degree_programs")
def show_degree_programs():
    all_degree_programs = DegreeProgram.query.all()
    return render_template("degree_programs.html", degree_programs=all_degree_programs)