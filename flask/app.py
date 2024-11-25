# app.py
from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import json
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)


class LabelManager:
    def __init__(self):
        self.labels = {0: {"name": "Unlabeled", "color": "lightblue"}}
        self.next_id = 1

    def add_label(self, name, color):
        self.labels[self.next_id] = {"name": name, "color": color}
        self.next_id += 1
        return self.next_id - 1

    def get_color_map(self):
        return {k: v["color"] for k, v in self.labels.items()}

    def get_label_options(self):
        return [
            {"label": f"{v['name']} ({k})", "value": k} for k, v in self.labels.items()
        ]


label_manager = LabelManager()

# Load data
df = pd.read_csv("location.csv")
df["label"] = 0


@app.route("/")
def index():
    return render_template(
        "index.html",
        data=df.to_dict("records"),
        labels=label_manager.labels,
        x_min=df["x"].min(),
        x_max=df["x"].max(),
        y_min=df["y"].min(),
        y_max=df["y"].max(),
    )


@app.route("/api/add_label", methods=["POST"])
def add_label():
    data = request.json
    label_id = label_manager.add_label(data["name"], data["color"])
    return jsonify({"id": label_id, "options": label_manager.get_label_options()})


@app.route("/api/update_labels", methods=["POST"])
def update_labels():
    data = request.json
    global df
    for point in data["points"]:
        mask = (df["x"] == point["x"]) & (df["y"] == point["y"])
        df.loc[mask, "label"] = data["label"]
    return jsonify({"success": True})


@app.route("/api/download_labels")
def download_labels():
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return send_file(buffer, download_name="labeled_data.csv", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
