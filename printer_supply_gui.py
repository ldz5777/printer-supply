#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机耗材分配和费用分摊程序 - GUI版本
支持 Windows 7 和 macOS

Python 3.7+ 兼容（Windows 7最高支持Python 3.8）
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# 数据文件路径
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


class PrinterSupplyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("打印机耗材分配与费用分摊")
        self.root.geometry("900x650")

        # 加载数据
        self.data = self.load_data()

        # 创建界面
        self.create_widgets()
        self.refresh_all()

    def load_data(self):
        """加载数据"""
        default_data = {
            "supplies": [],
            "allocations": [],
            "departments": ["行政部", "财务部", "技术部", "市场部"]
        }
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return default_data
        return default_data

    def save_data(self):
        """保存数据"""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title = tk.Label(self.root, text="打印机耗材分配与费用分摊系统",
                        font=("微软雅黑", 16, "bold"))
        title.pack(pady=10)

        # 创建笔记本（标签页）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # === 标签页1：耗材入库 ===
        frame1 = ttk.Frame(notebook)
        notebook.add(frame1, text=" 耗材入库 ")
        self.create_supply_frame(frame1)

        # === 标签页2：耗材分配 ===
        frame2 = ttk.Frame(notebook)
        notebook.add(frame2, text=" 耗材分配 ")
        self.create_allocate_frame(frame2)

        # === 标签页3：自动分摊 ===
        frame3 = ttk.Frame(notebook)
        notebook.add(frame3, text=" 自动分摊 ")
        self.create_auto_frame(frame3)

        # === 标签页4：报表统计 ===
        frame4 = ttk.Frame(notebook)
        notebook.add(frame4, text=" 报表统计 ")
        self.create_report_frame(frame4)

        # === 标签页5：部门管理 ===
        frame5 = ttk.Frame(notebook)
        notebook.add(frame5, text=" 部门管理 ")
        self.create_dept_frame(frame5)

    def create_supply_frame(self, parent):
        """耗材入库界面"""
        # 输入区域
        input_frame = tk.LabelFrame(parent, text="入库信息", font=("微软雅黑", 10))
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # 表单
        tk.Label(input_frame, text="耗材名称:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_name = tk.Entry(input_frame, width=25)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="类型:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.combo_type = ttk.Combobox(input_frame, values=["墨盒", "硒鼓", "打印纸", "色带", "其他"], width=15)
        self.combo_type.set("墨盒")
        self.combo_type.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(input_frame, text="数量:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_qty = tk.Entry(input_frame, width=25)
        self.entry_qty.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="单价(元):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.entry_price = tk.Entry(input_frame, width=15)
        self.entry_price.grid(row=1, column=3, padx=5, pady=5)

        # 按钮
        btn_frame = tk.Frame(parent)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text=" 入库 ", bg="#4CAF50", fg="white",
                 font=("微软雅黑", 11), command=self.add_supply).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=" 清空 ", command=self.clear_supply).pack(side=tk.LEFT, padx=5)

        # 列表
        list_frame = tk.LabelFrame(parent, text="入库记录")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("id", "name", "type", "qty", "price", "total", "date", "remain")
        self.tree_supply = ttk.Treeview(list_frame, columns=cols, show="headings", height=12)

        self.tree_supply.heading("id", text="编号")
        self.tree_supply.heading("name", text="名称")
        self.tree_supply.heading("type", text="类型")
        self.tree_supply.heading("qty", text="数量")
        self.tree_supply.heading("price", text="单价")
        self.tree_supply.heading("total", text="总成本")
        self.tree_supply.heading("date", text="入库日期")
        self.tree_supply.heading("remain", text="剩余")

        for col in cols:
            self.tree_supply.column(col, width=80, anchor="center")
        self.tree_supply.column("name", width=120)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_supply.yview)
        self.tree_supply.configure(yscrollcommand=scroll.set)

        self.tree_supply.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def create_allocate_frame(self, parent):
        """耗材分配界面"""
        # 选择区域
        select_frame = tk.LabelFrame(parent, text="分配信息")
        select_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(select_frame, text="选择耗材:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
        self.combo_supply = ttk.Combobox(select_frame, width=30, state="readonly")
        self.combo_supply.grid(row=0, column=1, padx=5, pady=10)

        tk.Label(select_frame, text="选择部门:").grid(row=1, column=0, padx=5, pady=10, sticky="e")
        self.combo_dept_alloc = ttk.Combobox(select_frame, width=20, state="readonly")
        self.combo_dept_alloc.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        tk.Label(select_frame, text="分配数量:").grid(row=2, column=0, padx=5, pady=10, sticky="e")
        self.entry_alloc_qty = tk.Entry(select_frame, width=15)
        self.entry_alloc_qty.grid(row=2, column=1, padx=5, pady=10, sticky="w")

        tk.Button(select_frame, text=" 执行分配 ", bg="#2196F3", fg="white",
                 font=("微软雅黑", 11), command=self.do_allocate).grid(row=3, column=1, pady=15, sticky="w")

        # 分配记录
        list_frame = tk.LabelFrame(parent, text="分配记录")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("date", "name", "dept", "qty", "price", "cost")
        self.tree_alloc = ttk.Treeview(list_frame, columns=cols, show="headings", height=15)

        self.tree_alloc.heading("date", text="日期")
        self.tree_alloc.heading("name", text="耗材名称")
        self.tree_alloc.heading("dept", text="部门")
        self.tree_alloc.heading("qty", text="数量")
        self.tree_alloc.heading("price", text="单价")
        self.tree_alloc.heading("cost", text="分摊费用")

        for col in cols:
            self.tree_alloc.column(col, width=100, anchor="center")
        self.tree_alloc.column("name", width=150)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_alloc.yview)
        self.tree_alloc.configure(yscrollcommand=scroll.set)

        self.tree_alloc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def create_auto_frame(self, parent):
        """自动分摊界面"""
        info = tk.Label(parent, text="按部门人数/打印量比例自动分摊费用",
                       font=("微软雅黑", 11), fg="#666")
        info.pack(pady=10)

        # 选择耗材
        top_frame = tk.Frame(parent)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(top_frame, text="选择耗材:").pack(side=tk.LEFT)
        self.combo_auto_supply = ttk.Combobox(top_frame, width=35, state="readonly")
        self.combo_auto_supply.pack(side=tk.LEFT, padx=5)

        # 权重输入
        weight_frame = tk.LabelFrame(parent, text="各部门权重（如人数、预估打印量）")
        weight_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.weight_entries = {}
        for i, dept in enumerate(self.data["departments"]):
            row = i // 3
            col = (i % 3) * 2
            tk.Label(weight_frame, text=f"{dept}:").grid(row=row, column=col, padx=10, pady=15, sticky="e")
            entry = tk.Entry(weight_frame, width=12)
            entry.insert(0, "1")
            entry.grid(row=row, column=col+1, padx=5, pady=15)
            self.weight_entries[dept] = entry

        # 按钮
        tk.Button(parent, text=" 开始自动分摊 ", bg="#FF9800", fg="white",
                 font=("微软雅黑", 12), command=self.do_auto_allocate).pack(pady=15)

        # 结果显示
        self.result_text = scrolledtext.ScrolledText(parent, width=80, height=12, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def create_report_frame(self, parent):
        """报表统计界面"""
        # 统计按钮
        btn_frame = tk.Frame(parent)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text=" 刷新报表 ", bg="#9C27B0", fg="white",
                 font=("微软雅黑", 11), command=self.refresh_report).pack()

        # 报表内容
        self.report_text = scrolledtext.ScrolledText(parent, width=90, height=30, font=("微软雅黑", 10))
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def create_dept_frame(self, parent):
        """部门管理界面"""
        # 当前部门
        list_frame = tk.LabelFrame(parent, text="当前部门列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.dept_listbox = tk.Listbox(list_frame, font=("微软雅黑", 12), height=10)
        self.dept_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 操作区域
        op_frame = tk.Frame(parent)
        op_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(op_frame, text="新部门名称:").pack(side=tk.LEFT)
        self.entry_new_dept = tk.Entry(op_frame, width=20)
        self.entry_new_dept.pack(side=tk.LEFT, padx=5)
        tk.Button(op_frame, text=" 添加 ", bg="#4CAF50", fg="white",
                 command=self.add_dept).pack(side=tk.LEFT, padx=5)
        tk.Button(op_frame, text=" 删除选中 ", bg="#f44336", fg="white",
                 command=self.del_dept).pack(side=tk.LEFT, padx=5)

    # ========== 功能方法 ==========

    def add_supply(self):
        """添加入库"""
        try:
            name = self.entry_name.get().strip()
            qty = int(self.entry_qty.get())
            price = float(self.entry_price.get())

            if not name or qty <= 0 or price < 0:
                messagebox.showerror("错误", "请填写正确的信息")
                return

            supply = {
                "id": len(self.data["supplies"]) + 1,
                "name": name,
                "type": self.combo_type.get(),
                "quantity": qty,
                "unit_price": price,
                "total_cost": qty * price,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "remaining": qty
            }

            self.data["supplies"].append(supply)
            self.save_data()
            self.refresh_all()

            messagebox.showinfo("成功", f"入库成功！\n总成本: {supply['total_cost']:.2f} 元")
            self.clear_supply()

        except ValueError:
            messagebox.showerror("错误", "数量和单价必须是数字")

    def clear_supply(self):
        """清空入库表单"""
        self.entry_name.delete(0, tk.END)
        self.entry_qty.delete(0, tk.END)
        self.entry_price.delete(0, tk.END)

    def do_allocate(self):
        """执行分配"""
        supply_str = self.combo_supply.get()
        dept = self.combo_dept_alloc.get()

        if not supply_str or not dept:
            messagebox.showerror("错误", "请选择耗材和部门")
            return

        try:
            qty = int(self.entry_alloc_qty.get())
        except:
            messagebox.showerror("错误", "数量必须是整数")
            return

        # 解析耗材ID
        supply_id = int(supply_str.split(".")[0])
        supply = next((s for s in self.data["supplies"] if s["id"] == supply_id), None)

        if not supply:
            messagebox.showerror("错误", "耗材不存在")
            return

        if qty > supply["remaining"]:
            messagebox.showerror("错误", f"库存不足，剩余 {supply['remaining']}")
            return

        # 创建分配记录
        allocation = {
            "id": len(self.data["allocations"]) + 1,
            "supply_id": supply_id,
            "supply_name": supply["name"],
            "department": dept,
            "quantity": qty,
            "unit_price": supply["unit_price"],
            "cost": qty * supply["unit_price"],
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        supply["remaining"] -= qty
        self.data["allocations"].append(allocation)
        self.save_data()
        self.refresh_all()

        messagebox.showinfo("成功", f"分配成功！\n费用: {allocation['cost']:.2f} 元")
        self.entry_alloc_qty.delete(0, tk.END)

    def do_auto_allocate(self):
        """自动按比例分摊"""
        supply_str = self.combo_auto_supply.get()
        if not supply_str:
            messagebox.showerror("错误", "请选择耗材")
            return

        supply_id = int(supply_str.split(".")[0])
        supply = next((s for s in self.data["supplies"] if s["id"] == supply_id), None)

        if not supply:
            messagebox.showerror("错误", "耗材不存在")
            return

        # 读取权重
        weights = {}
        total_weight = 0
        for dept, entry in self.weight_entries.items():
            try:
                w = float(entry.get() or 0)
                weights[dept] = w
                total_weight += w
            except:
                messagebox.showerror("错误", f"{dept} 的权重必须是数字")
                return

        if total_weight == 0:
            messagebox.showerror("错误", "权重总和不能为0")
            return

        # 执行分摊
        result = f"=== 自动分摊结果 ===\n"
        result += f"耗材: {supply['name']}\n"
        result += f"总成本: {supply['total_cost']:.2f} 元\n"
        result += f"总数量: {supply['quantity']}\n"
        result += "-" * 40 + "\n"

        for dept, weight in weights.items():
            if weight <= 0:
                continue
            ratio = weight / total_weight
            cost = supply["total_cost"] * ratio
            qty = max(1, int(supply["quantity"] * ratio))

            allocation = {
                "id": len(self.data["allocations"]) + 1,
                "supply_id": supply_id,
                "supply_name": supply["name"],
                "department": dept,
                "quantity": qty,
                "unit_price": supply["unit_price"],
                "cost": cost,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "method": "自动分摊"
            }
            self.data["allocations"].append(allocation)

            result += f"{dept}:\n"
            result += f"  权重: {weight} ({ratio*100:.1f}%)\n"
            result += f"  分摊费用: {cost:.2f} 元\n"
            result += f"  分配数量: {qty}\n\n"

        supply["remaining"] = 0
        self.save_data()
        self.refresh_all()

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)
        messagebox.showinfo("成功", "自动分摊完成！")

    def refresh_report(self):
        """刷新报表"""
        report = "=" * 60 + "\n"
        report += "           费用分摊报表\n"
        report += "=" * 60 + "\n\n"

        if not self.data["allocations"]:
            report += "暂无分配记录\n"
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report)
            return

        # 按部门汇总
        dept_costs = defaultdict(lambda: {"cost": 0, "count": 0})
        for alloc in self.data["allocations"]:
            dept_costs[alloc["department"]]["cost"] += alloc["cost"]
            dept_costs[alloc["department"]]["count"] += 1

        report += "【按部门汇总】\n"
        report += "-" * 40 + "\n"
        total = 0
        for dept, info in sorted(dept_costs.items()):
            report += f"{dept:12s}: {info['cost']:10.2f} 元  ({info['count']}次)\n"
            total += info["cost"]
        report += "-" * 40 + "\n"
        report += f"{'合计':12s}: {total:10.2f} 元\n\n"

        # 按耗材汇总
        supply_costs = defaultdict(float)
        for alloc in self.data["allocations"]:
            supply_costs[alloc["supply_name"]] += alloc["cost"]

        report += "【按耗材汇总】\n"
        report += "-" * 40 + "\n"
        for name, cost in sorted(supply_costs.items()):
            report += f"{name:15s}: {cost:10.2f} 元\n"
        report += "\n"

        # 明细
        report += "【分配明细】\n"
        report += "-" * 70 + "\n"
        report += f"{'日期':12s} {'耗材':12s} {'部门':10s} {'数量':8s} {'金额':10s}\n"
        report += "-" * 70 + "\n"

        for alloc in sorted(self.data["allocations"], key=lambda x: x["date"], reverse=True):
            report += f"{alloc['date']:12s} {alloc['supply_name']:12s} "
            report += f"{alloc['department']:10s} {alloc['quantity']:8d} {alloc['cost']:10.2f}\n"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report)

    def add_dept(self):
        """添加部门"""
        name = self.entry_new_dept.get().strip()
        if name and name not in self.data["departments"]:
            self.data["departments"].append(name)
            self.save_data()
            self.refresh_all()
            self.entry_new_dept.delete(0, tk.END)
            messagebox.showinfo("成功", f"已添加部门: {name}")

    def del_dept(self):
        """删除部门"""
        sel = self.dept_listbox.curselection()
        if sel:
            dept = self.dept_listbox.get(sel[0])
            if messagebox.askyesno("确认", f"确定删除部门 {dept} 吗？"):
                self.data["departments"].remove(dept)
                self.save_data()
                self.refresh_all()

    def refresh_all(self):
        """刷新所有显示"""
        # 刷新入库列表
        for item in self.tree_supply.get_children():
            self.tree_supply.delete(item)
        for s in self.data["supplies"]:
            self.tree_supply.insert("", tk.END, values=(
                s["id"], s["name"], s["type"], s["quantity"],
                f"{s['unit_price']:.2f}", f"{s['total_cost']:.2f}",
                s["date"], s["remaining"]
            ))

        # 刷新分配列表
        for item in self.tree_alloc.get_children():
            self.tree_alloc.delete(item)
        for a in self.data["allocations"]:
            self.tree_alloc.insert("", tk.END, values=(
                a["date"], a["supply_name"], a["department"],
                a["quantity"], f"{a['unit_price']:.2f}", f"{a['cost']:.2f}"
            ))

        # 刷新耗材下拉框
        supplies = [f"{s['id']}. {s['name']} (剩余{s['remaining']})"
                   for s in self.data["supplies"] if s["remaining"] > 0]
        self.combo_supply["values"] = supplies
        self.combo_auto_supply["values"] = [f"{s['id']}. {s['name']}" for s in self.data["supplies"]]

        # 刷新部门下拉框
        self.combo_dept_alloc["values"] = self.data["departments"]

        # 刷新部门列表
        self.dept_listbox.delete(0, tk.END)
        for d in self.data["departments"]:
            self.dept_listbox.insert(tk.END, d)

        # 刷新权重输入框
        for widget in self.weight_entries.values():
            widget.destroy()
        self.weight_entries.clear()

        # 重建权重输入
        for i, dept in enumerate(self.data["departments"]):
            if dept in self.weight_entries:
                continue
            # 找到父容器重新创建

        self.refresh_report()


def main():
    root = tk.Tk()
    # 设置样式（Windows 7 兼容）
    try:
        style = ttk.Style()
        style.theme_use("vista")  # Windows 7风格
    except:
        pass

    app = PrinterSupplyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
