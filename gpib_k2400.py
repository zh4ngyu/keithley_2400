import time
import tkinter
from tkinter.constants import BOTTOM, END, LEFT, RIGHT, TOP
from typing import Text
import pyvisa




class GUI_2400():
    def __init__(self, window, inst):
        self.window = window
        self.inst = inst


    def init_window(self):
        self.window.title('Keithley 2400 control')


        self.seq = []
        self.ramp_rate = 0.1
        self.ramp_step = 0.01
        self.status_str = ['OFF','ON']

        self.frame_seq = tkinter.Frame(self.window)
        self.frame_stat = tkinter.Frame(self.window)
        self.frame_op = tkinter.Frame(self.window)
        self.frame_rate = tkinter.Frame(self.window)

        self.listbox = tkinter.Listbox(self.frame_seq, yscrollcommand = True, width = 50, height = 40)
        self.editbox = tkinter.Text(self.frame_seq, yscrollcommand = True, width = 30, height = 40)

        self.button_run = tkinter.Button(self.frame_op, text = 'run', command = self.run_seq)
        self.button_refresh = tkinter.Button(self.frame_op, text = "refresh", command = self.listbox_refresh)

        self.status_label = tkinter.Label(self.frame_stat, text = self.status_str[self.get_stat()])
        self.status_switch = tkinter.Button(self.frame_stat, text = 'ON/OFF', command = self.change_stat)

        self.rate_label = tkinter.Label(self.frame_rate, text = 'ramp rate (V/s) =')
        self.rate_entry = tkinter.Entry(self.frame_rate)
        self.rate_entry.insert(0, self.ramp_rate)



        self.frame_seq.pack()
        self.editbox.pack(side = RIGHT)
        self.listbox.pack(side = LEFT)

        self.frame_stat.pack(side = LEFT)
        self.status_label.pack(side = LEFT)
        self.status_switch.pack(side = LEFT)

        self.frame_op.pack(side = RIGHT)
        self.button_refresh.pack(side = LEFT)
        self.button_run.pack(side = LEFT)

        self.frame_rate.pack()
        self.rate_label.pack(side = LEFT)
        self.rate_entry.pack(side = LEFT)


    def ramp_volt(self, volt):
        time_1 = time.perf_counter()

        ramp_step = self.ramp_step
        current_volt = self.get_volt()
        ramp_rate = self.ramp_rate

        step_time = ramp_step / ramp_rate
        step_num = round((volt - current_volt) / ramp_step)
        if step_num == 0:
            return

        step = step_num / abs(step_num) * ramp_step

        
        for i in range(abs(int(step_num))):
            self.change_volt(current_volt + (i+1) * step)
            time.sleep((i+1) * step_time - time.perf_counter() + time_1)
            


    def run_seq(self):
        self.listbox_refresh()
        time_0 = time.perf_counter()
        time_1 = time.perf_counter()
        timeline = 0
        
        seq = self.seq
        for i in range(len(seq)):
            current_volt = self.get_volt()
            line = seq[i].split()

            if (len(line) == 0):
                continue

            print('{}V->{}V'.format(round(current_volt,3), line[0]))
            self.ramp_volt(float(line[0]))
            ramp_time = time.perf_counter() - time_1

            if (len(line) == 1):
                print('ramp time: {}s'.format(ramp_time))
                timeline += ramp_time
                

            elif (len(line) == 2):
                hold_time = float(line[1]) - ramp_time
                timeline += float(line[1])
                if hold_time > 0:
                    print('ramp time: {}s, hold time: {}'.format(round(ramp_time,6), round(hold_time,6)))
                else:
                    print('ramp time: {}s'.format(ramp_time))
                time.sleep(max(0, timeline - time.perf_counter() + time_0))

            time_1 = time.perf_counter()
            

        print('finished----time elapsed {}s \n'.format(time.perf_counter()-time_0))
        self.listbox_refresh()


    def change_volt(self, volt):
        self.inst.write('SOUR:VOLT:LEV:IMM:AMPL {}'.format(volt))

    def get_volt(self):
        return float(self.inst.query(':SOURce:VOLTage?'))

    def set_rate(self,r):
        self.ramp_rate = r




    def get_text(self):
        raw = self.editbox.get('1.0', END)
        seq = raw.split('\n')
        for item in seq:
            line = item.split()
            for word in line:
                try:
                    float(word)
                except ValueError:
                    print('can not convert to numbers')
                    return

        raw = self.rate_entry.get()
        try:
            self.ramp_rate = float(raw)
        except ValueError:
            print('can not convert to numbers')
            return

        self.seq = seq
   

    def listbox_refresh(self):
        self.get_text()
        seq = self.seq
        last_volt = self.get_volt()
        ramp_rate = self.ramp_rate
        seq_str = []

        for i in range(len(seq)):
            line = seq[i].split()
            if (len(line) == 2):
                ramp_time = abs(last_volt - float(line[0])) / ramp_rate
                stay_time = float(line[1]) - ramp_time
                if ramp_time == 0:
                    seq_str.append('[{}V] {}s'.format(line[0], stay_time))
                else:
                    seq_str.append('[{}V->{}V] {}s     [{}V] {}s'.format(round(last_volt,6), line[0], round(ramp_time,6), line[0], round(stay_time,6)))
                    if stay_time <= 0:
                        seq_str.append('hold time less than 0, may cause wrong time line')
                last_volt = float(line[0])
            elif (len(line) == 1):
                ramp_time = abs(last_volt - float(line[0])) / ramp_rate
                if ramp_time == 0:
                    seq_str.append('no operation')
                else:
                    seq_str.append('[{}V->{}V] {}s'.format(round(last_volt,6), line[0], round(ramp_time,6)))
                last_volt = float(line[0])

        self.listbox.delete(0,END)
        for i in range(len(seq_str)):
            self.listbox.insert(i, seq_str[i])



    def get_stat(self):
        return int(self.inst.query('OUTP:STAT?'))

    def change_stat(self):
        print(self.get_stat() == 0)
        if self.get_stat() == 0:
            self.inst.write('OUTP:STAT ON')
        else:
            self.inst.write('OUTP:STAT OFF')
        self.status_label['text'] = self.status_str[self.get_stat()]

    def get_current(self):
        self.inst.write(':READ?')
        return (float(self.inst.read()[14:27]))





def gui_start(inst):
    window = tkinter.Tk()              #实例化出一个父窗口
    gui_2400 = GUI_2400(window, inst)
    gui_2400.init_window()

    window.mainloop()          #父窗口进入事件循环，可以理解为保持窗口运行，否则界面不展示



rm = pyvisa.ResourceManager()
inst = rm.open_resource('GPIB0::27::INSTR')

gui_start(inst)