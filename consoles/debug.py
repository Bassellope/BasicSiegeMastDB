from sbs_utils.procedural.gui import gui_row, gui_icon, gui_text

def debug_menu_template(item):
    gui_row("row-height: 48px;padding:3px")
    gui_icon(f"icon_index: {item['icon']};color:white;")
    gui_row("row-height: 1.2em")
    gui_text(f"$text:{item['text']};justify:left;")
    

def debug_dump_mast():
    from sbs_utils.helpers import FrameContext

    
    task = FrameContext.server_task
    _mast = task.main.mast 
    scheds = _mast.schedulers
    s = len(scheds)
    print(f"Scheduler count {s}")
    task_count = 0
    sub_task_count = 0

    active_labels = {}
    for s in scheds:
        for t in s.tasks:
            task_count += 1
            l = t.active_label
            lc = active_labels.get(l, 0)
            lc += 1
            active_labels[l] = lc
            for st in t.sub_tasks:
                sub_task_count += 1
                # May need recursion
    print(f"Task count {task_count} sub task count {sub_task_count}")
    for l in active_labels:
        c = active_labels[l]
        print(f"Label: {l} count: {c}")










