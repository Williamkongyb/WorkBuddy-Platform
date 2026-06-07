// gen_manual.js — 生成 WorkBuddy 短视频全自动带货 v3.2 操作手册
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak
} = require("docx");

// --- helpers ---
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
}
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: opts.after ?? 120 }, children: [new TextRun({ text, ...opts })] });
}
function code(text) {
  return new Paragraph({
    spacing: { after: 60, before: 60 },
    indent: { left: 360 },
    shading: { fill: "F5F5F5", type: ShadingType.CLEAR },
    children: [new TextRun({ text, font: "Consolas", size: 20 })]
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun(text)]
  });
}
function bulletBold(label, text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text: label, bold: true }), new TextRun(text)]
  });
}
function bulletCode(label, text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text: label, bold: true }), new TextRun({ text, font: "Consolas", size: 20 })]
  });
}
function makeRow(cells, header = false) {
  return new TableRow({
    children: cells.map((c, i) => new TableCell({
      borders,
      width: { size: c.w, type: WidthType.DXA },
      shading: header ? { fill: "1F4E79", type: ShadingType.CLEAR } : undefined,
      margins: cellMargins,
      children: [new Paragraph({
        spacing: { after: 0 },
        children: [new TextRun({ text: c.t, bold: header, color: header ? "FFFFFF" : "333333", size: header ? 20 : 18, font: header ? "Arial" : "Arial" })]
      })]
    }))
  });
}
function table(colWidths, rows) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colWidths,
    rows
  });
}

// Table widths – use 9360 total
function W(...arr) { return arr; }

const numbering = {
  config: [
    { reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }] },
    { reference: "numbers",
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ]
};

// ---- BUILD DOCUMENT ----
const children = [];

// Cover
children.push(new Paragraph({ spacing: { before: 3000 } }));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [new TextRun({ text: "WorkBuddy \u77ed\u89c6\u9891\u5168\u81ea\u52a8\u5e26\u8d27", size: 52, bold: true, font: "Arial", color: "1F4E79" })]
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [new TextRun({ text: "\u64cd\u4f5c\u624b\u518c", size: 40, bold: true, font: "Arial", color: "2E75B6" })]
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 100 },
  children: [new TextRun({ text: "v3.2  \u4e94\u6bb5\u5f0f\u5168\u81ea\u52a8\u5316\u95ed\u73af", size: 24, color: "666666" })]
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 600 },
  children: [new TextRun({ text: "\u667a\u80fd\u6587\u6848 \u2192 \u89c6\u9891\u5236\u4f5c \u2192 \u591a\u5e73\u53f0\u53d1\u5e03 \u2192 \u6570\u636e\u76d1\u63a7 \u2192 \u6df1\u5ea6\u590d\u76d8", size: 20, color: "888888" })]
}));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "2026\u5e745\u670827\u65e5\u7248", size: 20, color: "AAAAAA" })] }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// TOC
children.push(new Paragraph({
  spacing: { after: 400 },
  children: [new TextRun({ text: "\u76ee\u5f55", size: 36, bold: true, color: "1F4E79" })]
}));
children.push(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第一部分 ======
children.push(h1("一、WorkBuddy 对话触发 —— 最便捷的启动方式"));
children.push(p("\u8fd9\u662f\u63a8\u8350\u7684\u9996\u9009\u65b9\u5f0f\uff1a\u76f4\u63a5\u5728 WorkBuddy \u5bf9\u8bdd\u4e2d\u8bf4\u4e00\u53e5\u8bdd\uff0cAI \u81ea\u52a8\u52a0\u8f7d\u6280\u80fd\u5e76\u6267\u884c\u5b8c\u6574\u6d41\u7a0b\u3002\u4e0d\u9700\u8981\u8bb0\u4f4f\u4efb\u4f55\u547d\u4ee4\u884c\u53c2\u6570\uff0c\u7528\u81ea\u7136\u8bed\u8a00\u5373\u53ef\u3002"));

h2("1.1 一键全流程触发");
table(W(4680, 4680), [
  makeRow([{t: "\u89e6\u53d1\u8bcd", w: 2000}, {t: "\u6548\u679c", w: 7360}], true),
  makeRow([{t: "\u201c\u5f00\u59cb\u4eca\u65e5\u5e26\u8d27\u201d", w: 2000}, {t: "\u542f\u52a8\u5b8c\u6574\u4e94\u6bb5\u5f0f\u95ed\u73af\uff0c\u4ece\u6587\u6848\u751f\u6210\u5230\u6570\u636e\u590d\u76d8\u4e00\u6c14\u5475\u6210", w: 7360}]),
  makeRow([{t: "\u201c\u4e00\u952e\u751f\u6210\u77ed\u89c6\u9891\u201d", w: 2000}, {t: "\u540c\u4e0a\uff0c\u5feb\u901f\u542f\u52a8\u5168\u6d41\u7a0b", w: 7360}]),
  makeRow([{t: "\u201c\u5168\u81ea\u52a8\u526a\u8f91\u53d1\u5e03\u201d", w: 2000}, {t: "\u540c\u4e0a\uff0c\u53e6\u4e00\u4e2a\u5e38\u7528\u89e6\u53d1\u8bcd", w: 7360}]),
]);

h2("1.2 分步触发（单步执行）");
table(W(3000, 6360), [
  makeRow([{t: "\u89e6\u53d1\u8bcd", w: 3000}, {t: "\u6267\u884c\u5185\u5bb9", w: 6360}], true),
  makeRow([{t: "\u201c\u4ec5\u751f\u6210\u6587\u6848\u201d / \u201c\u751f\u6210\u5e26\u8d27\u6587\u6848 [\u4ea7\u54c1\u540d]\u201d", w: 3000}, {t: "\u53ea\u8dd1\u6587\u6848\u751f\u6210 + \u5408\u89c4\u81ea\u68c0", w: 6360}]),
  makeRow([{t: "\u201c\u4ec5\u5236\u4f5c\u89c6\u9891\u201d", w: 3000}, {t: "\u53ea\u8dd1\u89c6\u9891\u5236\u4f5c\uff08\u526a\u6620\u6570\u5b57\u4eba\uff09", w: 6360}]),
  makeRow([{t: "\u201c\u4ec5\u53d1\u5e03\u201d", w: 3000}, {t: "\u53ea\u8dd1\u591a\u5e73\u53f0\u53d1\u5e03", w: 6360}]),
  makeRow([{t: "\u201c\u6253\u5f00\u4e2d\u63a7\u53f0\u201d", w: 3000}, {t: "\u542f\u52a8 Web \u63a7\u5236\u9762\u677f (http://localhost:5888)", w: 6360}]),
  makeRow([{t: "\u201c\u6253\u5f00\u684c\u9762\u4e2d\u63a7\u53f0\u201d", w: 3000}, {t: "\u542f\u52a8\u72ec\u7acb\u684c\u9762 GUI\uff08CustomTkinter\uff09", w: 6360}]),
]);

h2("1.3 增强工具触发");
table(W(3000, 6360), [
  makeRow([{t: "\u89e6\u53d1\u8bcd", w: 3000}, {t: "\u5bf9\u5e94\u5de5\u5177", w: 6360}], true),
  makeRow([{t: "\u201c\u62fc\u63a5\u89c6\u9891\u201d / \u201c\u5408\u5e76\u89c6\u9891\u7247\u6bb5\u201d", w: 3000}, {t: "\u65b9\u6cd5\u4e00\uff1aFFmpeg \u65e0\u635f\u62fc\u63a5", w: 6360}]),
  makeRow([{t: "\u201c\u56fe\u6587\u6210\u7247\u201d / \u201c\u6587\u6848\u8f6c\u89c6\u9891\u201d", w: 3000}, {t: "\u65b9\u6cd5\u4e8c\uff1a\u526a\u6620\u56fe\u6587\u6210\u7247", w: 6360}]),
  makeRow([{t: "\u201c\u753b\u4e2d\u753b\u5408\u6210\u201d / \u201c\u53e0\u52a0\u89c6\u9891\u201d", w: 3000}, {t: "\u65b9\u6cd5\u4e09\uff1a\u6570\u5b57\u4eba+\u80cc\u666f\u5408\u6210", w: 6360}]),
  makeRow([{t: "\u201c\u6570\u636e\u76d1\u63a7\u201d / \u201c\u63a8\u6d41\u5206\u6790\u201d / \u201c\u8bc4\u8bba\u6d1e\u5bdf\u201d", w: 3000}, {t: "\u65b9\u6cd5\u56db\uff1a\u6570\u636e\u76d1\u63a7\u4e0e\u53d8\u73b0\u95ed\u73af", w: 6360}]),
  makeRow([{t: "\u201c\u8fd0\u8425\u76d1\u63a7\u201d / \u201c\u6df1\u5ea6\u590d\u76d8\u201d / \u201c\u5f02\u5e38\u9884\u8b66\u201d", w: 3000}, {t: "\u65b9\u6cd5\u4e94\uff1aAI\u8d85\u7ea7\u5458\u5de5\u8fd0\u8425\u76d1\u63a7\u6df1\u5ea6\u5f15\u64ce", w: 6360}]),
]);

children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第二部分 ======
children.push(h1("二、桌面中控台 GUI —— 可视化图形操作"));
children.push(p("\u684c\u9762\u4e2d\u63a7\u53f0\u662f\u4e00\u4e2a\u72ec\u7acb\u7684 Windows \u5e94\u7528\u7a0b\u5e8f\uff0c\u57fa\u4e8e CustomTkinter \u73b0\u4ee3 UI \u6846\u67b6\uff0c\u63d0\u4f9b\u76f4\u89c2\u7684\u56fe\u5f62\u5316\u64cd\u4f5c\u754c\u9762\u3002"));

h2("2.1 启动方式");
bulletBold("\u65b9\u5f0f\u4e00\uff08\u63a8\u8350\uff09\uff1a\u53cc\u51fb ", "D:\\WB_Workflow\\\u542f\u52a8\u684c\u9762\u4e2d\u63a7\u53f0.bat");
bulletBold("\u65b9\u5f0f\u4e8c\uff1a\u547d\u4ee4\u884c\uff0c", "cd D:\\WB_Workflow\\scripts && py main_gui.py");
bulletBold("\u65b9\u5f0f\u4e09\uff1a\u5728 WorkBuddy \u4e2d\u8bf4\uff0c", "\u201c\u6253\u5f00\u684c\u9762\u4e2d\u63a7\u53f0\u201d");

h2("2.2 界面布局");
table(W(3000, 6360), [
  makeRow([{t: "\u533a\u57df", w: 3000}, {t: "\u529f\u80fd", w: 6360}], true),
  makeRow([{t: "\u5de6\u4fa7\u5bfc\u822a\u680f", w: 3000}, {t: "\u4e09\u4e2a\u9875\u9762\u4e00\u952e\u5207\u6362\uff1a\u4efb\u52a1\u914d\u7f6e | \u89c4\u5219\u7ba1\u7406 | \u7cfb\u7edf\u65e5\u5fd7", w: 6360}]),
  makeRow([{t: "\u9876\u90e8\u5916\u89c2\u8bbe\u7f6e", w: 3000}, {t: "\u6df1\u8272/\u6d45\u8272/\u7cfb\u7edf\u81ea\u9002\u5e94 + \u5546\u52a1\u84dd/\u79d1\u6280\u7d2b/\u9ad8\u7ea7\u7070\u5b9e\u65f6\u5207\u6362\uff0c\u65e0\u9700\u91cd\u542f", w: 6360}]),
  makeRow([{t: "\u53f3\u4fa7\u5185\u5bb9\u533a", w: 3000}, {t: "\u7ba1\u9053\u4e09\u9636\u6bb5\u53ef\u89c6\u5316 + \u8fdb\u5ea6\u6761 + \u72b6\u6001\u706f", w: 6360}]),
  makeRow([{t: "\u63a7\u5236\u9762\u677f", w: 3000}, {t: "\u4ea7\u54c1\u540d/\u9009\u9898\u8f93\u5165\u3001\u56db\u5e73\u53f0\u591a\u9009\u3001\u53cc\u5f15\u64ce\u5207\u6362\u3001Dry Run\u5f00\u5173", w: 6360}]),
  makeRow([{t: "\u589e\u5f3a\u5de5\u5177\u533a", w: 3000}, {t: "\u62fc\u63a5/\u753b\u4e2d\u753b/\u56fe\u6587\u6210\u7247/\u6570\u636e\u76d1\u63a7/\u8fd0\u8425\u590d\u76d8\u5feb\u6377\u5165\u53e3", w: 6360}]),
  makeRow([{t: "\u5e95\u90e8\u72b6\u6001\u680f", w: 3000}, {t: "\u5b9e\u65f6\u65e5\u5fd7\u6eda\u52a8 + \u8fd0\u884c\u72b6\u6001\u63d0\u793a", w: 6360}]),
]);

h2("2.3 快捷键");
table(W(2000, 7360), [
  makeRow([{t: "\u5feb\u6377\u952e", w: 2000}, {t: "\u529f\u80fd", w: 7360}], true),
  makeRow([{t: "Ctrl+F", w: 2000}, {t: "\u4e00\u952e\u542f\u52a8\u5168\u6d41\u7a0b\uff08\u6587\u6848\u2192\u89c6\u9891\u2192\u53d1\u5e03\uff09", w: 7360}]),
  makeRow([{t: "F5", w: 2000}, {t: "\u5237\u65b0\u754c\u9762\u72b6\u6001", w: 7360}]),
  makeRow([{t: "Esc", w: 2000}, {t: "\u53d6\u6d88\u5f53\u524d\u4efb\u52a1", w: 7360}]),
]);

h2("2.4 实时换肤");
p("\u70b9\u51fb\u9876\u90e8\u4e0b\u62c9\u83dc\u5355\uff0c\u9009\u62e9\u4e3b\u9898\u8272\uff1a");
bullet("\u5546\u52a1\u84dd\uff08\u9ed8\u8ba4\uff09\u2014\u2014 \u4e13\u4e1a\u7a33\u91cd\u98ce\u683c");
bullet("\u79d1\u6280\u7d2b\u2014\u2014 \u79d1\u6280\u611f\u3001\u6d3b\u529b\u98ce\u683c");
bullet("\u9ad8\u7ea7\u7070\u2014\u2014 \u6781\u7b80\u5546\u52a1\u98ce\u683c");
bullet("\u6df1\u8272/\u6d45\u8272/\u7cfb\u7edf\u81ea\u9002\u5e94\u2014\u2014 \u8ddf\u968f Windows \u7cfb\u7edf\u4e3b\u9898");
p("\u5207\u6362\u5373\u65f6\u751f\u6548\uff0c\u65e0\u9700\u91cd\u542f\u7a0b\u5e8f\u3002");

children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第三部分 ======
children.push(h1("三、命令行操作（Orchestrator）—— 高级用户首选"));
children.push(p("Orchestrator \u662f\u6574\u4e2a\u5de5\u4f5c\u6d41\u7684\u4e3b\u7f16\u6392\u5668\uff0c\u652f\u6301\u4e30\u5bcc\u7684\u547d\u4ee4\u884c\u53c2\u6570\uff0c\u9002\u5408\u9ad8\u7ea7\u7528\u6237\u548c\u811a\u672c\u5316\u573a\u666f\u3002"));

h2("3.1 全流程命令");
code("cd C:\\Users\\Confu\\.workbuddy\\skills\\\u77ed\u89c6\u9891\u5168\u81ea\u52a8\u5e26\u8d27\\scripts");
code("py orchestrator.py --product \"\u667a\u80fd\u624b\u8868\"");
p("");

h2("3.2 完整参数速查表");
table(W(5500, 3860), [
  makeRow([{t: "\u53c2\u6570\u793a\u4f8b", w: 5500}, {t: "\u8bf4\u660e", w: 3860}], true),
  makeRow([{t: "py orchestrator.py --product \"XXX\"", w: 5500}, {t: "\u5168\u6d41\u7a0b\uff0c\u81ea\u52a8\u9009\u9898", w: 3860}]),
  makeRow([{t: "py orchestrator.py --product \"XXX\" --topic \"\u5065\u5eb7\"", w: 5500}, {t: "\u6307\u5b9a\u9009\u9898", w: 3860}]),
  makeRow([{t: "py orchestrator.py --product \"XXX\" --seedance", w: 5500}, {t: "\u4f7f\u7528 Seedance \u5f15\u64ce", w: 3860}]),
  makeRow([{t: "py orchestrator.py --product \"XXX\" --dry-run", w: 5500}, {t: "\u6a21\u62df\u8fd0\u884c\uff0c\u4e0d\u5b9e\u9645\u64cd\u4f5c", w: 3860}]),
  makeRow([{t: "py orchestrator.py --step generate", w: 5500}, {t: "\u4ec5\u751f\u6210\u6587\u6848", w: 3860}]),
  makeRow([{t: "py orchestrator.py --step make_video", w: 5500}, {t: "\u4ec5\u5236\u4f5c\u89c6\u9891", w: 3860}]),
  makeRow([{t: "py orchestrator.py --step publish", w: 5500}, {t: "\u4ec5\u53d1\u5e03", w: 3860}]),
  makeRow([{t: "py orchestrator.py --status", w: 5500}, {t: "\u67e5\u770b\u7ba1\u9053\u72b6\u6001", w: 3860}]),
]);

h2("3.3 增强工具命令行");
h3("\u65b9\u6cd5\u4e00\uff1a\u65e0\u635f\u62fc\u63a5");
code("py orchestrator.py --method concat --input-dir D:\\Clips --output \u4eca\u65e5\u53e3\u64ad.mp4");

h3("\u65b9\u6cd5\u4e8c\uff1a\u526a\u6620\u56fe\u6587\u6210\u7247");
code("py orchestrator.py --method t2v --script D:\\script.txt");
code("py orchestrator.py --method t2v --text \"\u4eca\u5929\u63a8\u8350...\" --output \u53e3\u64ad.mp4");

h3("\u65b9\u6cd5\u4e09\uff1a\u753b\u4e2d\u753b\u5408\u6210");
code("py orchestrator.py --method pip --fg D:\\Clips --bg D:\\Backgrounds --output \u753b\u4e2d\u753b.mp4");
code("py orchestrator.py --method pip --fg clip.mp4 --bg bg.jpg --scale 0.4 --position \"10:10\"");

h3("\u65b9\u6cd5\u56db\uff1a\u6570\u636e\u76d1\u63a7");
code("py orchestrator.py --method monitor");
code("py orchestrator.py --method monitor --dry-run");

h3("\u65b9\u6cd5\u4e94\uff1aAI\u8d85\u7ea7\u5458\u5de5");
code("py orchestrator.py --method super_employee        \u2192 \u5b8c\u6574\u8fd0\u884c\uff08\u6293\u53d6+\u9884\u8b66+\u590d\u76d8\uff09");
code("py ai_super_employee.py --mode scrape              \u2192 \u4ec5\u6570\u636e\u6293\u53d6");
code("py ai_super_employee.py --mode alert               \u2192 \u4ec5\u5f02\u5e38\u9884\u8b66");
code("py ai_super_employee.py --mode report --date 2026-05-26 \u2192 \u590d\u76d8\u6307\u5b9a\u65e5\u671f");
code("py ai_super_employee.py --dry-run                  \u2192 \u6a21\u62df\u8fd0\u884c");

children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第四部分 ======
children.push(h1("四、独立 EXE 运行 —— 无需 Python 环境"));
children.push(p("2026\u5e745\u670827\u65e5\u65b0\u6253\u5305\u7684 4 \u4e2a\u72ec\u7acb .exe \u6587\u4ef6\uff0c\u53ef\u4ee5\u76f4\u63a5\u53cc\u51fb\u8fd0\u884c\uff0c\u4e0d\u9700\u8981\u5b89\u88c5 Python \u6216\u4efb\u4f55\u4f9d\u8d56\u3002"));

h2("4.1 EXE 清单");
table(W(2000, 7360), [
  makeRow([{t: "EXE \u540d\u79f0", w: 2000}, {t: "\u5927\u5c0f\u4e0e\u7528\u9014", w: 7360}], true),
  makeRow([{t: "\u667a\u80fd\u6587\u6848\u751f\u6210.exe", w: 2000}, {t: "23.9 MB \u2014 \u7eaf Python\uff0c\u751f\u6210\u56db\u5e73\u53f0\u5dee\u5f02\u5316\u6587\u6848 + \u5408\u89c4\u81ea\u68c0\u3002\u7528\u6cd5\uff1a\u667a\u80fd\u6587\u6848\u751f\u6210.exe --product \"LED\u53f0\u706f\"", w: 7360}]),
  makeRow([{t: "\u526a\u6620\u6570\u5b57\u4eba\u89c6\u9891.exe", w: 2000}, {t: "56.8 MB \u2014 \u542b pyautogui\uff0c\u81ea\u52a8\u64cd\u63a7\u526a\u6620\u4e13\u4e1a\u7248\u5236\u4f5c\u6570\u5b57\u4eba\u89c6\u9891\u3002\u9996\u6b21\u4f7f\u7528\u9700\u2014calibrate\u6821\u51c6\u5750\u6807", w: 7360}]),
  makeRow([{t: "Seedance\u89c6\u9891\u5236\u4f5c.exe", w: 2000}, {t: "223.1 MB \u2014 \u542b opencv+numpy+edge_tts\uff0c\u706b\u5c71\u5f15\u64ce Seedance 2.0 API \u5907\u9009\u65b9\u6848\u3002\u9700\u8981 ARK_API_KEY + FFmpeg", w: 7360}]),
  makeRow([{t: "\u591a\u5e73\u53f0\u81ea\u52a8\u53d1\u5e03.exe", w: 2000}, {t: "164.9 MB \u2014 \u542b Playwright\uff0c\u81ea\u52a8\u767b\u5f55\u6296\u97f3/\u5c0f\u7ea2\u4e66/B\u7ad9\u53d1\u5e03\u3002\u9700\u8981 playwright install chromium", w: 7360}]),
]);

h2("4.2 EXE 位置与用法");
bullet("\u6240\u6709 .exe \u4f4d\u4e8e\uff1aD:\\WB_Workflow\\dist\\\u5404\u81ea\u6587\u4ef6\u5939\\");
bullet("\u53cc\u51fb .exe \u76f4\u63a5\u8fd0\u884c\uff0c\u6216\u5728\u547d\u4ee4\u884c\u4e2d\u5e26\u53c2\u6570\u8fd0\u884c");
bullet("\u8fd0\u884c\u65f6\u81ea\u52a8\u8bfb\u53d6 D:\\WB_Workflow\\config.json \u914d\u7f6e");

h2("4.3 重新打包");
p("\u82e5\u6e90\u7801\u66f4\u65b0\u540e\u9700\u8981\u91cd\u65b0\u6253\u5305\uff0c\u4f7f\u7528\u6784\u5efa\u5de5\u5177\uff1a");
code("cd D:\\WB_Workflow");
code("py build_all_exe.py                    \u2192 \u6253\u5305\u5168\u90e8 4 \u4e2a");
code("py build_all_exe.py --only 1,3         \u2192 \u53ea\u6253\u5305\u6307\u5b9a\u7f16\u53f7");
code("py build_all_exe.py --clean            \u2192 \u6e05\u7406\u540e\u6253\u5305");

children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第五部分 ======
children.push(h1("五、五种增强工具详解"));
children.push(p("\u4ee5\u4e0b\u4e94\u79cd\u589e\u5f3a\u5de5\u5177\u53ef\u4ee5\u72ec\u7acb\u4f7f\u7528\uff0c\u4e5f\u53ef\u4ee5\u901a\u8fc7 Orcherstrator \u4e00\u952e\u8c03\u7528\u3002"));

h2("5.1 方法一：FFmpeg 无损拼接");
bulletBold("\u89e6\u53d1\u8bcd\uff1a", "\u201c\u62fc\u63a5\u89c6\u9891\u201d\u3001\u201c\u5408\u5e76\u89c6\u9891\u7247\u6bb5\u201d\u3001\u201c\u65e0\u635f\u62fc\u63a5 MP4\u201d");
bulletBold("\u539f\u7406\uff1a", "\u626b\u63cf\u6587\u4ef6\u5939\u5185\u6240\u6709 MP4 \u7247\u6bb5 \u2192 \u751f\u6210\u5217\u8868\u6587\u4ef6 \u2192 FFmpeg concat \u5206\u79bb\u5668\u6a21\u5f0f\uff08-c copy \u96f6\u753b\u8d28\u635f\u5931\uff09");
bulletBold("\u4f18\u52bf\uff1a", "\u6781\u901f\u3001\u96f6\u753b\u8d28\u635f\u5931\uff0c\u9002\u5408\u5408\u5e76\u591a\u6bb5\u5df2\u7f16\u7801\u7684\u89c6\u9891");
code("py orchestrator.py --method concat --input-dir D:\\Clips --output \u4eca\u65e5\u53e3\u64ad_\u6700\u7ec8\u7248.mp4");

h2("5.2 方法二：剪映图文成片");
bulletBold("\u89e6\u53d1\u8bcd\uff1a", "\u201c\u56fe\u6587\u6210\u7247\u201d\u3001\u201c\u6587\u6848\u8f6c\u89c6\u9891\u201d\u3001\u201c\u526a\u6620\u56fe\u6587\u6210\u7247\u201d");
bulletBold("\u539f\u7406\uff1a", "pyautogui \u81ea\u52a8\u5316\u64cd\u63a7\u526a\u6620 \u2192 \u70b9\u51fb\u201c\u56fe\u6587\u6210\u7247\u201d \u2192 \u7c98\u8d34\u6587\u6848 \u2192 \u9009\u62e9\u6570\u5b57\u4eba \u2192 \u751f\u6210 \u2192 \u5bfc\u51fa 1080p");
bulletBold("\u6ce8\u610f\uff1a", "\u9700\u8981\u526a\u6620\u4e13\u4e1a\u7248\u5df2\u5b89\u88c5\u5e76\u767b\u5f55");
code("py orchestrator.py --method t2v --text \"\u4eca\u5929\u63a8\u8350...\" --output \u53e3\u64ad.mp4");

h2("5.3 方法三：画中画合成");
bulletBold("\u89e6\u53d1\u8bcd\uff1a", "\u201c\u753b\u4e2d\u753b\u5408\u6210\u201d\u3001\u201c\u53e0\u52a0\u89c6\u9891\u201d\u3001\u201c\u6570\u5b57\u4eba+\u80cc\u666f\u5408\u6210\u201d");
bulletBold("\u539f\u7406\uff1a", "\u80cc\u666f\u7f29\u653e\u4e3a 1920x1080 \u5168\u5c4f \u2192 \u6570\u5b57\u4eba\u89c6\u9891\u7f29\u653e\u5230\u6307\u5b9a\u6bd4\u4f8b \u2192 overlay \u6ee4\u955c\u53e0\u52a0\u5230\u6307\u5b9a\u4f4d\u7f6e");
bulletBold("\u5e38\u7528\u573a\u666f\uff1a", "\u6570\u5b57\u4eba\u53e3\u64ad + \u5546\u54c1\u5c55\u793a\u80cc\u666f\u5408\u6210");
code("py orchestrator.py --method pip --fg clip.mp4 --bg bg.jpg --scale 0.4 --position \"10:10\"");

h2("5.4 方法四：数据监控与变现闭环");
bulletBold("\u89e6\u53d1\u8bcd\uff1a", "\u201c\u6570\u636e\u76d1\u63a7\u201d\u3001\u201c\u67e5\u770b\u6628\u65e5\u6570\u636e\u201d\u3001\u201c\u63a8\u6d41\u5206\u6790\u201d\u3001\u201c\u8bc4\u8bba\u6d1e\u5bdf\u201d\u3001\u201c\u53d8\u73b0\u95ed\u73af\u201d");
bulletBold("\u529f\u80fd\uff1a", "Playwright \u81ea\u52a8\u6293\u53d6\u6296\u97f3/\u5c0f\u7ea2\u4e66/B\u7ad9\u6628\u65e5\u89c6\u9891\u6570\u636e \u2192 \u8ba1\u7b97\u63a8\u6d41\u6307\u6570\uff08\u5b8c\u64ad\u7387>30%\u4e14\u70b9\u8d5e\u7387>3%\uff09 \u2192 \u8fbe\u6807\u201c\u5efa\u8bae\u6295\u6d41\u201d \u2192 \u8bc4\u8bba\u533a\u9ad8\u9891\u95ee\u9898\u63d0\u53d6+\u56de\u590d\u8349\u7a3f");
bulletBold("\u8f93\u51fa\uff1a", "\u7ed3\u6784\u5316\u76d1\u63a7\u62a5\u544a\u5230 reports/");
code("py orchestrator.py --method monitor              \u2192 \u5b8c\u6574\u76d1\u63a7");
code("py orchestrator.py --method monitor --dry-run    \u2192 \u6a21\u62df\u8fd0\u884c");

h2("5.5 方法五：AI 超级员工运营监控深度引擎");
bulletBold("\u89e6\u53d1\u8bcd\uff1a", "\u201c\u8fd0\u8425\u76d1\u63a7\u201d\u3001\u201c\u6df1\u5ea6\u590d\u76d8\u201d\u3001\u201c\u5f02\u5e38\u9884\u8b66\u201d\u3001\u201csuper employee\u201d\u3001\u201c\u5168\u7ef4\u5ea6\u6570\u636e\u201d");

p("\u4e09\u5927\u6a21\u5757\uff1a");
const empRows = [
  makeRow([{t: "\u6a21\u5757", w: 2500}, {t: "\u529f\u80fd", w: 3360}, {t: "\u660e\u7ec6", w: 3500}], true),
  makeRow([{t: "\u2460 \u5168\u7ef4\u5ea6\u6570\u636e\u6293\u53d6", w: 2500}, {t: "\u57fa\u7840\u4e92\u52a8 5 \u9879 + \u6df1\u5ea6\u8d28\u91cf 5 \u9879", w: 3360}, {t: "\u64ad\u653e/\u70b9\u8d5e/\u8bc4\u8bba/\u8f6c\u53d1/\u6536\u85cf + \u5b8c\u64ad\u7387/5s\u5b8c\u64ad/2s\u8df3\u51fa/\u5747\u64ad\u65f6\u957f\uff0cSQLite \u6301\u4e45\u5316", w: 3500}]),
  makeRow([{t: "\u2461 \u5f02\u5e38\u9650\u6d41\u9884\u8b66", w: 2500}, {t: "\u52a8\u6001\u9608\u503c + LLM \u81ea\u52a8\u8bca\u65ad", w: 3360}, {t: "2h\u64ad\u653e<500 / \u5b8c\u64ad\u7387\u4f4e\u4e8e\u5747\u503c30% / 2s\u8df3\u51fa>65% \u2192 \u7591\u4f3c\u9650\u6d41\u6807\u8bb0", w: 3500}]),
  makeRow([{t: "\u2462 \u6bcf\u65e5\u590d\u76d8\u62a5\u544a", w: 2500}, {t: "LLM \u5f52\u56e0\u5206\u6790 + \u4f18\u5316\u5efa\u8bae + \u591a\u6e20\u9053\u63a8\u9001", w: 3360}, {t: "\u81ea\u52a8\u751f\u6210 Markdown \u62a5\u544a\uff0c\u652f\u6301\u4f01\u5fae/\u9489\u9489/\u98de\u4e66\u63a8\u9001", w: 3500}]),
];
children.push(table(W(2500, 3360, 3500), empRows));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第六部分 ======
children.push(h1("六、定时自动化任务"));
children.push(p("\u4ee5\u4e0b\u5b9a\u65f6\u4efb\u52a1\u5df2\u914d\u7f6e\u5e76\u81ea\u52a8\u8fd0\u884c\uff0c\u65e0\u9700\u624b\u52a8\u5e72\u9884\uff1a"));

table(W(2500, 3000, 3860), [
  makeRow([{t: "\u4efb\u52a1\u540d\u79f0", w: 2500}, {t: "\u6267\u884c\u65f6\u95f4", w: 3000}, {t: "\u5185\u5bb9", w: 3860}], true),
  makeRow([{t: "\u6bcf\u65e5\u8fd0\u8425\u76d1\u63a7\u6df1\u5ea6\u590d\u76d8", w: 2500}, {t: "\u6bcf\u65e5 8:00 AM", w: 3000}, {t: "AI\u8d85\u7ea7\u5458\u5de5\u5f15\u64ce\u5168\u7ef4\u5ea6\u8fd0\u884c\uff1a\u6570\u636e\u6293\u53d6\u2192\u5f02\u5e38\u9884\u8b66\u2192LLM\u590d\u76d8\u62a5\u544a", w: 3860}]),
  makeRow([{t: "\u6bcf\u65e5\u6570\u636e\u76d1\u63a7\u4e0e\u53d8\u73b0\u95ed\u73af", w: 2500}, {t: "\u6bcf\u65e5 10:00 AM", w: 3000}, {t: "\u6293\u53d6\u6628\u65e5\u89c6\u9891\u6570\u636e\u2192\u63a8\u6d41\u6307\u6570\u5206\u6790\u2192\u8bc4\u8bba\u6d1e\u5bdf\u2192\u6295\u6d41\u5efa\u8bae+\u56de\u590d\u8349\u7a3f", w: 3860}]),
]);

h2("6.1 Web 中控台");
p("\u53e6\u5916\u8fd8\u63d0\u4f9b\u4e24\u79cd\u8f85\u52a9\u4e2d\u63a7\u53f0\uff1a");
bulletBold("Web \u5728\u7ebf\u9762\u677f\uff1a", "\u6d4f\u89c8\u5668\u8bbf\u95ee http://localhost:5888\uff0c\u63d0\u4f9b\u6587\u6848\u9884\u89c8/\u7ba1\u9053\u72b6\u6001/\u53d1\u5e03\u76d1\u63a7/\u4e00\u952e\u5168\u6d41\u7a0b");
bulletBold("\u79bb\u7ebf HTML \u9762\u677f\uff1a", "\u53cc\u51fb D:\\WB_Workflow\\\u4e2d\u63a7\u53f0-\u79bb\u7ebf\u7248.html\uff0c\u65e0\u9700 Flask \u670d\u52a1\u5373\u53ef\u67e5\u770b\u7ba1\u9053\u72b6\u6001");
code("\u542f\u52a8 Web \u670d\u52a1\uff1apy scripts/dashboard_server.py");

children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第七部分 ======
children.push(h1("七、配置文件说明"));
children.push(p("\u6240\u6709\u914d\u7f6e\u53c2\u6570\u5206\u5e03\u5728\u4e24\u4e2a\u6587\u4ef6\u4e2d\uff0c\u65b9\u4fbf\u7075\u6d3b\u5b9a\u5236\uff1a"));

h2("7.1 主配置文件");
table(W(2500, 6860), [
  makeRow([{t: "\u6587\u4ef6", w: 2500}, {t: "\u7528\u9014", w: 6860}], true),
  makeRow([{t: "D:\\WB_Workflow\\config.json", w: 2500}, {t: "\u4e3b\u914d\u7f6e\u6587\u4ef6\uff0c7\u5927\u914d\u7f6e\u57df\u3001280\u884c\u3002\u5305\u542b\uff1a\u5168\u5c40\u53c2\u6570\u3001\u6587\u6848\u751f\u6210\u3001\u89c6\u9891\u5236\u4f5c\u3001\u53d1\u5e03\u5e73\u53f0\u3001\u5408\u89c4\u89c4\u5219\u3001\u76d1\u63a7\u9608\u503c\u3001\u8d85\u7ea7\u5458\u5de5", w: 6860}]),
  makeRow([{t: "scripts/config.yaml", w: 2500}, {t: "\u6280\u80fd\u5185\u90e8\u914d\u7f6e\uff0c\u5305\u542b\u5f15\u64ce\u53c2\u6570\u3001\u4e2d\u63a7\u53f0\u7aef\u53e3\u3001\u91cd\u8bd5\u7b56\u7565\u3001\u5de5\u5177\u53c2\u6570", w: 6860}]),
]);

h2("7.2 config.json 关键配置域");
table(W(2500, 6860), [
  makeRow([{t: "\u914d\u7f6e\u57df", w: 2500}, {t: "\u5305\u542b\u5185\u5bb9", w: 6860}], true),
  makeRow([{t: "global", w: 2500}, {t: "\u5de5\u4f5c\u76ee\u5f55\u3001\u8f93\u51fa\u76ee\u5f55\u3001\u91cd\u8bd5\u7b56\u7565", w: 6860}]),
  makeRow([{t: "generate", w: 2500}, {t: "\u6587\u6848\u751f\u6210\u5f15\u64ce\u3001\u5408\u89c4\u5ba1\u67e5\u914d\u7f6e\u3001\u5e73\u53f0\u89c4\u5219\u6587\u4ef6\u8def\u5f84", w: 6860}]),
  makeRow([{t: "video", w: 2500}, {t: "\u4e3b\u5f15\u64ce\uff08\u526a\u6620\uff09\u548c\u5907\u9009\u5f15\u64ce\uff08Seedance\uff09\u53c2\u6570\uff0c\u5305\u542b ARK_API_KEY", w: 6860}]),
  makeRow([{t: "publish", w: 2500}, {t: "\u53d1\u5e03\u5e73\u53f0\u5217\u8868\u3001\u5b89\u5168\u6682\u505c\u65f6\u957f\u3001\u6d4f\u89c8\u5668\u6570\u636e\u8def\u5f84\u3001\u91cd\u590d\u53d1\u5e03\u68c0\u6d4b\u8bb0\u5f55\u4fdd\u5b58\u8def\u5f84", w: 6860}]),
  makeRow([{t: "compliance", w: 2500}, {t: "\u8fdd\u7981\u8bcd\u89c4\u5219\u5e93\u6587\u4ef6\u8def\u5f84\u3001\u81ea\u52a8\u4fee\u590d\u7b56\u7565\u3001\u5e73\u53f0\u7279\u6b8a\u89c4\u5219", w: 6860}]),
  makeRow([{t: "monitor", w: 2500}, {t: "\u63a8\u6d41\u6307\u6570\u9608\u503c\uff08\u5b8c\u64ad\u7387>30%,\u70b9\u8d5e\u7387>3%\uff09\u3001\u6570\u636e\u6293\u53d6\u5ef6\u8fdf", w: 6860}]),
  makeRow([{t: "super_employee", w: 2500}, {t: "\u5f02\u5e38\u9608\u503c\u3001LLM\u914d\u7f6e\u3001\u63a8\u9001\u6e20\u9053\uff08\u4f01\u5fae/\u9489\u9489/\u98de\u4e66\uff09\u3001SQLite\u6570\u636e\u5e93\u8def\u5f84", w: 6860}]),
]);

h2("7.3 合规规则库");
bulletBold("\u6587\u4ef6\u4f4d\u7f6e\uff1a", "D:\\WB_Workflow\\platform_rules.txt");
bulletBold("\u5185\u5bb9\uff1a", "5\u5e73\u53f0\u89c4\u5219\u5e93\uff08\u6296\u97f3/\u5feb\u624b/\u5c0f\u7ea2\u4e66/\u89c6\u9891\u53f7/\u54d4\u54e9\u54d4\u54e9\uff09\uff0c\u542b B\u7ad9\u4e13\u5c5e4\u9879\u89c4\u5219 + 19\u4e2a B\u7ad9\u5173\u952e\u8bcd");
bulletBold("\u5207\u6362\u65b9\u6cd5\uff1a", "\u4fee\u6539 config.json \u4e2d compliance.rules_file \u5373\u53ef\u6362\u89c4\u5219\u6587\u4ef6\uff0c\u65e0\u9700\u6539\u4ee3\u7801");

children.push(new Paragraph({ children: [new PageBreak()] }));

// ====== 第八部分 ======
children.push(h1("八、快速排障"));
table(W(3500, 5860), [
  makeRow([{t: "\u95ee\u9898", w: 3500}, {t: "\u89e3\u51b3\u65b9\u6848", w: 5860}], true),
  makeRow([{t: "\u4e2d\u6587\u4e71\u7801\u6216 emoji \u62a5\u9519", w: 3500}, {t: "\u786e\u8ba4\u811a\u672c\u5df2\u6ce8\u5165 safe_print\uff0c\u6216\u5728\u547d\u4ee4\u884c\u524d\u52a0 chcp 65001 \u5207\u6362\u5230 UTF-8", w: 5860}]),
  makeRow([{t: "FFmpeg \u627e\u4e0d\u5230", w: 3500}, {t: "\u786e\u4fdd FFmpeg \u5df2\u5b89\u88c5\u5e76\u52a0\u5165\u7cfb\u7edf PATH\uff0c\u6216\u5c06 ffmpeg.exe \u653e\u5230 C:\\ffmpeg\\bin\\", w: 5860}]),
  makeRow([{t: "\u526a\u6620\u81ea\u52a8\u5316\u5931\u8d25", w: 3500}, {t: "\u9996\u6b21\u4f7f\u7528\u9700\u2014calibrate \u6821\u51c6\u5750\u6807\uff0c\u786e\u4fdd\u526a\u6620\u4e13\u4e1a\u7248\u5df2\u767b\u5f55\u4e14\u7a97\u53e3\u4e0d\u88ab\u906e\u6321", w: 5860}]),
  makeRow([{t: "Playwright \u627e\u4e0d\u5230\u6d4f\u89c8\u5668", w: 3500}, {t: "\u8fd0\u884c playwright install chromium \u5b89\u88c5\u6d4f\u89c8\u5668\u5185\u6838", w: 5860}]),
  makeRow([{t: "\u53d1\u5e03\u5931\u8d25", w: 3500}, {t: "\u68c0\u67e5\u662f\u5426\u9700\u8981\u91cd\u65b0\u767b\u5f55\uff08\u767b\u5f55\u6001\u8fc7\u671f\uff09\uff0c\u67e5\u770b browser_data/ \u76ee\u5f55\u662f\u5426\u5b58\u5728", w: 5860}]),
  makeRow([{t: "Seedance API \u62a5\u9519", w: 3500}, {t: "\u786e\u8ba4 config.json \u4e2d\u5df2\u914d\u7f6e ARK_API_KEY\uff0c\u68c0\u67e5\u53c2\u8003\u56fe ref_image.jpg \u662f\u5426\u5b58\u5728\u4e8e D:\\WB_Workflow\\", w: 5860}]),
  makeRow([{t: "EXE \u8fd0\u884c\u62a5\u9519\u201cargs not defined\u201d", w: 3500}, {t: "\u5df2\u4fee\u590d\uff08\u667a\u80fd\u6587\u6848\u751f\u6210.exe \u5df2\u91cd\u65b0\u6253\u5305\uff09\uff0c\u5176\u4ed6 3 \u4e2a EXE \u65e0\u6b64\u95ee\u9898", w: 5860}]),
  makeRow([{t: "\u6784\u5efa\u5de5\u5177\u8fd0\u884c\u62a5\u9519", w: 3500}, {t: "\u4f7f\u7528 build_all_exe.py --clean \u6e05\u7406\u540e\u91cd\u8bd5\uff0c\u786e\u4fdd PyInstaller 6.20+ \u5df2\u5b89\u88c5", w: 5860}]),
]);

children.push(new Paragraph({ spacing: { before: 600 } }));
children.push(p(""));

// ----- assemble -----
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1F4E79" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E75B6" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "333333" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering,
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "WorkBuddy \u77ed\u89c6\u9891\u5168\u81ea\u52a8\u5e26\u8d27 v3.2 \u64cd\u4f5c\u624b\u518c", size: 16, color: "999999" })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "\u7b2c ", size: 16, color: "999999" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "999999" }), new TextRun({ text: " \u9875", size: 16, color: "999999" })]
        })]
      })
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  const out = "D:\\WB_Workflow\\WorkBuddy\u5de5\u4f5c\u6d41\u64cd\u4f5c\u624b\u518c_v3.2.docx";
  fs.writeFileSync(out, buf);
  console.log("OK -> " + out);
});
