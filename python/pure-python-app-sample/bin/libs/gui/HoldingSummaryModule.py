import os,calendar,time,subprocess,re
from datetime import date,datetime

from Tkinter import *
from tkFileDialog import asksaveasfilename,askopenfilename

from libs.modules.common.models.FundManager import FundManager
from libs.modules.mis.MISCacheUpdater import MISCacheUpdater
from libs.modules.summary.FundSummaryGenerator import FundSummaryGenerator
from libs.utils.FundManagerCacheDownloadThread import FundManagerCacheDownloadThread
from libs.gui.elements.ProgBar import ProgBar



class HoldingSummaryModule:
    def __init__(self,root,props):
        self.final_funds = [762605,762635,370761,370751,370775,370745,370753,370755,370759]
        self.pass_through_funds = [571779,571781,572179,764579,571819,763955,571699,763957,571979,571981,571985,571859,571739,571741,536699,634859,664139,571987,571899,536701]
        self.def_network_cache_path = props.data['NET_CACHE_PATH']
        self.def_local_cache_path = props.data['CACHE_PATH']
        self.def_output_path = props.data['OUTPUT_PATH']
        self.root = root
        
        self.early_terminate = False
        self.fundman = FundManager()
        self.cache_dates = props.data['MIS_DATES']
        if len(self.cache_dates) > 0:
            self.cache_most_recent_date = self.cache_dates[0]
        else:
            self.cache_most_recent_date = "N/A"
        
        self.months = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
        self.months_rev = []
        for var in range(len(self.months)-1,-1,-1):
            self.months_rev.append(self.months[var])
        self.years = []
        for i in range(1990,datetime.now().year+1):
            self.years.append(i)
        self.years = tuple(self.years)
            
    def runHoldingSummary(self,option_frame):
        self.option_frame = option_frame
        self.buildDataOptions()
             
        label_frame = LabelFrame(self.option_frame,text="Report Options",padx=5)
        label_frame.pack(fill=BOTH,padx=5,pady=5,expand=1)
        
        tmp_frame = Frame(label_frame)
        Label(tmp_frame, text="Specify Final Funds").pack(side=LEFT)
        Button(tmp_frame, text=".....", command=self.selectFinalFunds).pack(side=LEFT,padx=42)
        tmp_frame.pack(fill=X,pady=3) 
        
        tmp_frame = Frame(label_frame)
        Label(tmp_frame, text="Verify Pass-Through Funds").pack(side=LEFT)
        Button(tmp_frame, text=".....", command=self.selectPassThroughFunds).pack(side=LEFT,padx=5)
        tmp_frame.pack(fill=X,pady=3)
        
        self.sort_by = IntVar()
        self.sort_order = IntVar()
        
        tmp_frame_ab = LabelFrame(label_frame)
        
        tmp_frame_a = Frame(tmp_frame_ab)
        tmp_frame = Frame(tmp_frame_a)
        Label(tmp_frame, text="Sort By: ").pack(side=LEFT,padx=5)
        tmp_frame.pack(fill=X,pady=3)
        tmp_frame = Frame(tmp_frame_a)
        Radiobutton(tmp_frame,text="Total MCP",variable=self.sort_by,value=0).pack(side=LEFT,padx=15)
        tmp_frame.pack(fill=X)
        tmp_frame = Frame(tmp_frame_a)
        Radiobutton(tmp_frame,text="Total Non-MCP",variable=self.sort_by,value=1).pack(side=LEFT,padx=15)
        tmp_frame.pack(fill=X)
        tmp_frame = Frame(tmp_frame_a)
        tmp_r = Radiobutton(tmp_frame,text="Overall Total",variable=self.sort_by,value=2)
        tmp_r.select()
        tmp_r.pack(side=LEFT,padx=15)
        tmp_frame.pack(side=LEFT)
        tmp_frame_a.pack(side=LEFT,fill=BOTH)
        
        tmp_frame_b = Frame(tmp_frame_ab)
        tmp_frame = Frame(tmp_frame_b)
        Label(tmp_frame, text="Sort Order: ").pack(side=LEFT,padx=5)
        tmp_frame.pack(fill=X,pady=3)
        tmp_frame = Frame(tmp_frame_b)
        Radiobutton(tmp_frame,text="Least-to-Greatest",variable=self.sort_order,value=0).pack(side=LEFT,padx=15)
        tmp_frame.pack(fill=X)
        tmp_r = Radiobutton(tmp_frame_b,text="Greatest-to-Least",variable=self.sort_order,value=1)
        tmp_r.select()
        tmp_r.pack(side=LEFT,padx=15)
        tmp_frame.pack(fill=X)
        tmp_frame_b.pack(side=LEFT,fill=BOTH)
                        
        tmp_frame_ab.pack(fill=X)
        
        tmp_frame = Frame(label_frame)
        Label(tmp_frame, text="Column Order").pack(side=LEFT)
        Button(tmp_frame, text=".....", command=self.selectColOrder).pack(side=LEFT,padx=67)
        tmp_frame.pack(fill=X,pady=3)
        
        self.report_out_path = StringVar()
        tmp_frame = Frame(label_frame)
        Label(tmp_frame,text="Export to: ").pack(side=LEFT)
        self.path_entry = Entry(tmp_frame, textvariable=self.report_out_path)
        self.path_entry.insert(0, self.def_output_path + "HoldingSummary.pdf")
        self.path_entry.pack(side=LEFT,padx=5,expand=1,fill=X)
        Button(tmp_frame, text="Browse...", command=self.setOutputPath).pack(side=LEFT,padx=5)
        tmp_frame.pack(fill=X,pady=3)
        
        self.export_type = IntVar()
        tmp_frame = Frame(label_frame)
        Checkbutton(tmp_frame,text = "Export to Excel",variable=self.export_type).pack(side=LEFT,padx=5)
        tmp_frame.pack(fill=X)      
             
        Button(self.option_frame,text="Generate Report",command=self.generateHoldingSummary).pack(side=BOTTOM,pady=9)
    
    def buildDataOptions(self):
        data_frame = LabelFrame(self.option_frame,text="Data Source Options",padx=5,pady=5)
        data_frame.pack(fill=X,padx=5)
        
        tmp_frame = Frame(data_frame)
        Label(tmp_frame, text="Select Data Source:").pack(side=LEFT)
        tmp_frame.pack(fill=X)
        
        self.data_input_type = IntVar()
        tmp_frame = Frame(data_frame)
        if self.cache_most_recent_date != "N/A":
            self.data_input_button1 = Radiobutton(tmp_frame,text="Most recent cached data     (" + self.cache_most_recent_date.strftime("%m/%d/%Y") + ")",command=self.activateCacheButton,variable=self.data_input_type,value=1)
        else:
            self.data_input_button1 = Radiobutton(tmp_frame,text="Most recent cached data     (N/A)",command=self.activateCacheButton,variable=self.data_input_type,value=1)
        self.data_input_button1.select()
        self.MIS_cache_path = self.def_network_cache_path + "MIS/current"
        self.data_input_button1.pack(side=LEFT,padx=10)
        tmp_frame.pack(fill=X)
        
        tmp_frame = Frame(data_frame)
        self.data_input_button3 = Radiobutton(tmp_frame, text="Historically cached data",command=self.activateCacheButton,variable=self.data_input_type,value=3)
        self.data_input_button3.pack(side=LEFT,padx=10)
    
        self.cache_month_var = StringVar()
        self.cache_month_box = Spinbox(tmp_frame,state=DISABLED,command=self.updateCacheDates,textvariable=self.cache_month_var,width=5)
        self.cache_year_var = StringVar()
        self.cache_year_box = Spinbox(tmp_frame,state=DISABLED,command=self.updateCacheDates,textvariable=self.cache_year_var,width=5)
        self.cache_month_box.pack(side=LEFT)
        self.cache_year_box.pack(side=LEFT,padx=10)
        tmp_frame.pack(fill=X)
        
        self.updateCacheDates(True)
        
        tmp_frame = Frame(data_frame)
        Label(tmp_frame,text = "------ OR ------").pack(side=LEFT,padx=50,pady=5)
        tmp_frame.pack(fill=X)
        
        tmp_frame = Frame(data_frame)
        self.data_input_button2 = Radiobutton(tmp_frame, text="Backstop Server (may take a while)",command=self.activateCacheButton,variable=self.data_input_type,value=2)
        self.data_input_button2.pack(side=LEFT,padx=10)
        tmp_frame.pack(fill=X)
        
        self.as_of_date = StringVar()
        tmp_frame = Frame(data_frame)
        self.as_of_label = Label(tmp_frame, text="As Of Date:", state=DISABLED)
        self.as_of_label.pack(side=LEFT,padx=5)
        
        self.cur_month = StringVar()
        self.cur_year = StringVar()
        
        self.as_of_date_month = Spinbox(tmp_frame, state=DISABLED, values=self.months_rev[self.prevMonth():len(self.months_rev)], textvariable=self.cur_month, width=5)
        self.as_of_date_year = Spinbox(tmp_frame, state=DISABLED, values=self.years, textvariable=self.cur_year,command=self.updateAsOfDate, width=5)
        self.as_of_date_month.pack(side=LEFT)
        self.as_of_date_year.pack(side=LEFT)
        
        self.cur_month.set(self.months[self.prevMonth()])
        self.cur_year.set(self.prevMonthYear(0))        
        self.as_of_date = self.getEndOfMonth(self.prevMonth(), self.prevMonthYear(0))  
                                                  
        tmp_frame.pack(fill=X,pady=3, padx=20)
    
    def activateCacheButton(self):
        if self.data_input_type.get() == 3:
            self.cache_month_box.config(state=NORMAL)
            self.cache_year_box.config(state=NORMAL)
            self.as_of_date_month.config(state=DISABLED)
            self.as_of_date_year.config(state=DISABLED)
            self.as_of_label.config(state=DISABLED)
        elif self.data_input_type.get() == 2:
            self.cache_month_box.config(state=DISABLED)
            self.cache_year_box.config(state=DISABLED)
            self.MIS_cache_path = self.def_local_cache_path + "MIS/current"
            self.as_of_date_month.config(state=NORMAL)
            self.as_of_date_year.config(state=NORMAL)
            self.as_of_label.config(state=NORMAL)
        else:
            self.cache_month_box.config(state=DISABLED)
            self.cache_year_box.config(state=DISABLED)
            self.MIS_cache_path = self.def_network_cache_path + "MIS/current"
            self.as_of_date_month.config(state=DISABLED)
            self.as_of_date_year.config(state=DISABLED)
            self.as_of_label.config(state=DISABLED)
    
    def updateCacheDates(self,init=False):
        if init:
            cur_m = self.months[self.cache_most_recent_date.month-1]
            cur_y = str(self.cache_most_recent_date.year)
        else:
            cur_m = self.cache_month_var.get()
            cur_y = self.cache_year_var.get()
        cache_years = []
        cache_months = []
        cache_month_index = []
        for d in self.cache_dates:
            if self.months[d.month-1] == cur_m:
                if d.year not in cache_years:
                    cache_years.append(d.year)
            if int(d.year) == int(cur_y):                
                if (d.month-1) not in cache_month_index:
                    cache_month_index.append((d.month-1))
        cache_years = sorted(cache_years)
        cache_month_index = sorted(cache_month_index)
        
        for m in cache_month_index:
            cache_months.append(self.months[m])
        
        tmp = cache_months
        cache_months = []
        for var in range(len(tmp)-1,-1,-1):
            cache_months.append(tmp[var])
        
        self.cache_month_box.config(values=tuple(cache_months))
        self.cache_year_box.config(values=tuple(cache_years))
        
        self.cache_month_var.set(cur_m)
        self.cache_year_var.set(cur_y) 
    
    def updateDate(self, cur_month, cur_year, tmp_month_box):
        cur_month_lit = cur_month.get()
        cur_year_lit = cur_year.get()
        if int(cur_year_lit) == datetime.now().year and int(cur_year_lit) in self.years:
            tmp_month_box.delete(0,END)
            tmp_month_box.config(values=self.months_rev[self.prevMonth():len(self.months_rev)],textvariable=cur_month)
            if cur_month_lit in self.months_rev[0:self.prevMonth()]:
                cur_month.set(self.months_rev[self.prevMonth()])
            else:
                cur_month.set(cur_month_lit)
        else:
            tmp_month_box.delete(0,END)
            tmp_month_box.config(values=self.months_rev,textvariable=cur_month)
            cur_month.set(cur_month_lit)
    
    def updateAsOfDate(self):
        self.updateDate(self.cur_month, self.cur_year, self.as_of_date_month)
        
    def selectFinalFunds(self):
        self.fund_win = Toplevel()
        self.fund_win.title("Final Funds")
        
        self.entity_frame = Frame(self.fund_win,bd=1,relief=RAISED)
        tmp_frame = Frame(self.entity_frame)
        
        title = Label(tmp_frame,text="Specify the \"Final Funds\":")
        title.pack()
        tmp_frame.pack()
        
        if not os.access(self.MIS_cache_path + "/reports/product_rep.cache",os.F_OK):
            m = MISCacheUpdater(self.MIS_cache_path)
            as_of_date = datetime.strptime(self.as_of_date_entry.get(),"%m/%d/%Y")
            m.loadProductData(as_of_date)
        
        if self.fundman.cache_path != self.MIS_cache_path:
            self.fundman.setCachePath(self.MIS_cache_path)
            self.fundman.loadProductData()
        elif not self.fundman.loaded[1]:
            self.fundman.loadProductData() 
                
        self.prods = self.fundman.products
        self.checkbox_values = {}
        
        for p_id in sorted(self.prods.keys()):
            p = self.prods[p_id]
            tmp_frame = Frame(self.entity_frame)
            self.checkbox_values[p_id] = IntVar()
            tmp_checkbox = Checkbutton(tmp_frame,text = p.name,variable=self.checkbox_values[p_id])
            if p_id in self.final_funds:
                tmp_checkbox.select()
            tmp_checkbox.pack(side=LEFT)
            tmp_frame.pack(fill=X)
        
        self.entity_frame.pack(fill=X)
        Button(self.fund_win, text="OK", command=self.saveFinalFunds,width=10).pack(side=BOTTOM)
        
        self.resizeWindow(300, len(self.prods.keys())*22 + 50, self.fund_win)
    
    def saveFinalFunds(self):
        final_funds = []
        for p_id in self.prods.keys():
            if self.checkbox_values[p_id].get():
                final_funds.append(p_id)
        self.final_funds = final_funds
        self.fund_win.destroy()
    
    def selectPassThroughFunds(self):
        self.fund_win = Toplevel()
        self.fund_win.title("Pass-Through Funds")
        
        self.entity_frame = Frame(self.fund_win,bd=1,relief=RAISED)
        tmp_frame = Frame(self.entity_frame)
        
        title = Label(tmp_frame,text="Verify the \"Pass-Through Funds\":")
        title.pack()
        tmp_frame.pack()
        
        if not os.access(self.MIS_cache_path + "/reports/product_rep.cache",os.F_OK):
            m = MISCacheUpdater(self.MIS_cache_path)
            as_of_date = date.today()
            m.loadProductData(as_of_date)
        
        if self.fundman.cache_path != self.MIS_cache_path:
            self.fundman.setCachePath(self.MIS_cache_path)
            self.fundman.loadProductData()
        elif not self.fundman.loaded[1]:
            self.fundman.loadProductData() 
                
        self.prods = self.fundman.products
        self.checkbox_values = {}
        
        for p_id in sorted(self.prods.keys()):
            p = self.prods[p_id]
            tmp_frame = Frame(self.entity_frame)
            self.checkbox_values[p_id] = IntVar()
            tmp_checkbox = Checkbutton(tmp_frame,text = p.name,variable=self.checkbox_values[p_id])
            if p_id in self.pass_through_funds:
                tmp_checkbox.select()
            tmp_checkbox.pack(side=LEFT)
            tmp_frame.pack(fill=X)
        
        self.entity_frame.pack(fill=X)
        Button(self.fund_win, text="OK", command=self.savePassThroughFunds, width=10).pack(side=BOTTOM)
        
        self.resizeWindow(300, len(self.prods.keys())*22 + 50, self.fund_win)
    
    def savePassThroughFunds(self):
        pass_through_funds = []
        for p_id in self.prods.keys():
            if self.checkbox_values[p_id].get():
                pass_through_funds.append(p_id)
        self.pass_through_funds = pass_through_funds
        self.fund_win.destroy()
    
    def selectColOrder(self,refresh=False):
        if not refresh:
            self.fund_win = Toplevel()
            self.fund_win.title("Fund Order")
        
            if not os.access(self.MIS_cache_path + "/reports/product_rep.cache",os.F_OK):
                m = MISCacheUpdater(self.MIS_cache_path)
                as_of_date = date.today()
                m.loadProductData(as_of_date)
        
            if self.fundman.cache_path != self.MIS_cache_path:
                self.fundman.setCachePath(self.MIS_cache_path)
                self.fundman.loadProductData()
            elif not self.fundman.loaded[1]:
                self.fundman.loadProductData()
        
        self.fund_win_frame = Frame(self.fund_win)        
        self.entity_frame = Frame(self.fund_win_frame,bd=1,relief=RAISED)
        tmp_frame = Frame(self.entity_frame)
        title = Label(tmp_frame,text="Define the Column Order:")
        title.pack()
        tmp_frame.pack()             
                
        self.prods = self.fundman.products
        self.disp_rank_values = {}
        
        final_prods = []
        for f in self.final_funds:
            final_prods.append(self.prods[f])
        
        final_prods = sorted(final_prods,key=lambda product: product.disp_rank)
        
        for var in range(0,len(final_prods)):
            p = final_prods[var]
            tmp_frame = Frame(self.entity_frame)
            self.disp_rank_values[p.backstop_id] = StringVar()
            Label(tmp_frame,text=p.name).pack(side=LEFT)
            tmp_entry = Spinbox(tmp_frame,textvariable=self.disp_rank_values[p.backstop_id],command=self.saveDispRank,width=2,from_=0, to=(len(final_prods)+1))
            self.disp_rank_values[p.backstop_id].set(var+1)
            self.fundman.products[p.backstop_id].disp_rank = var+1
            tmp_entry.pack(side=RIGHT)
            tmp_frame.pack(fill=X)
        
        self.entity_frame.pack(fill=X)
        Button(self.fund_win_frame, text="OK", command=self.setDispRank, width=10).pack(side=BOTTOM)
        self.fund_win_frame.pack(fill=BOTH,expand=1)
        
        self.resizeWindow(300, len(final_prods)*22 + 50, self.fund_win)

    def saveDispRank(self):
        for p_id in self.disp_rank_values.keys():
            cur_rank = self.fundman.products[p_id].disp_rank
            new_rank = int(self.disp_rank_values[p_id].get())
            if cur_rank < new_rank:
                new_rank = cur_rank - 2 
            elif cur_rank > new_rank:
                new_rank = cur_rank + 2
            self.fundman.products[p_id].disp_rank = new_rank
        self.fund_win_frame.destroy()
        self.selectColOrder(True)
    
    def setDispRank(self):
        self.fund_win.destroy()
        
    def setOutputPath(self):
        path = asksaveasfilename(defaultextension=".pdf")
        self.path_entry.delete(0,END)
        self.path_entry.insert(0, path)
        
    def compareHoldingSummary(self):
        ref_data_path = askopenfilename()
        pass
    
    def generateHoldingSummary(self):
        map = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        
        self.pg = ProgBar("Loading...")
        
        if self.data_input_type.get() == 1:
            as_of_date = self.cache_most_recent_date
            self.MIS_cache_path = self.def_network_cache_path + "MIS/archived/" + self.cache_most_recent_date.strftime("%Y-%m-%d")
        elif self.data_input_type.get() == 2:
            tmp_date = date(int(self.cur_year.get()),map[self.cur_month.get()],1)
            as_of_date = datetime(tmp_date.year,tmp_date.month,self.getEndOfMonth(tmp_date.month, tmp_date.year))
            self.downloadCache(as_of_date)
        elif self.data_input_type.get() == 3:
            tmp_date = date(int(self.cache_year_var.get()),map[self.cache_month_var.get()],1)
            as_of_date = datetime(tmp_date.year,tmp_date.month,self.getEndOfMonth(tmp_date.month, tmp_date.year))
            self.MIS_cache_path = self.def_network_cache_path + "MIS/archived/" + as_of_date.strftime("%Y-%m-%d")
        
        if not self.early_terminate:
            self.loadFundMan()
            time.sleep(.25)
            
            self.pg.exit()
            del self.pg
            
            self.fundman.processFinalFunds(self.final_funds)
            self.fundman.processPassThroughFunds(self.pass_through_funds)
            
            path = self.report_out_path.get()
            f = FundSummaryGenerator(self.fundman)
            
            if self.export_type.get() == 0:
                f.generateReport(self.sort_by.get(),self.sort_order.get(),path,as_of_date)
                subprocess.Popen("\"" + path + "\"", shell=True)
            else:
                path = path.split(".")[0]
                path += ".xls"
                filename = path.split("/")
                
                filename = filename[len(filename)-1]
                rep_path = path[0:len(path)-len(filename)]
                
                f.exportToExcel(self.sort_by.get(),self.sort_order.get(),rep_path,filename)
        else:
            del self.pg
            self.early_terminate = False
            
    def downloadCache(self,as_of_date):
        self.pg.cur_sub_proc_total = 26.666
        m = MISCacheUpdater(self.MIS_cache_path,self.pg)
        load_arr = [True,True,False,False,False,False,False,True,False,False,False]
        self.downloadThread = FundManagerCacheDownloadThread(m,as_of_date,load_arr)
        self.downloadThread.start()
                
        for var in range(1,4):
            while self.downloadThread.status == var and not self.early_terminate:
                self.root.update()
                try:
                    self.pg.redisplay()
                except SystemExit:
                    self.downloadThread.terminate()
                    self.early_terminate = True
                time.sleep(.1)
        if self.early_terminate:
            del self.downloadThread
            del m
    
    def loadFundMan(self):
        self.fundman.setCachePath(self.MIS_cache_path)
        self.fundman.reset()
        
        self.pg.addMessage("Loading fund data...........")
        self.fundman.loadFundData()
        if self.data_input_type.get() in [1,3]: 
            self.pg.updateMainPercent(10.0)
        else:
            self.pg.updateMainPercent(90.0)
        self.pg.redisplay()
        self.pg.addMessage("Loading product data...........")
        self.fundman.loadProductData()
        if self.data_input_type.get() in [1,3]: 
            self.pg.updateMainPercent(20.0)
        else:
            self.pg.updateMainPercent(93.0)
        self.pg.redisplay()
        self.pg.addMessage("Loading holding data...........")
        self.fundman.loadHoldingsData()
        if self.data_input_type.get() in [1,3]: 
            self.pg.updateMainPercent(100.0)
        else:
            self.pg.updateMainPercent(100.0)
        self.pg.redisplay()
    
    def resizeWindow(self,x,y,win):
        self.win_w = x
        self.win_h = y
        
        screen_w = (win.winfo_screenwidth()-self.win_w) / 2
        screen_h = (win.winfo_screenheight()-self.win_h) / 2
        
        win.geometry(str(self.win_w)+'x'+str(self.win_h)+'+'+str(screen_w)+'+'+str(screen_h))
    
    def moveWindow(self,x,y,win):
        dx = x
        dy = y
        
        screen_w = (win.winfo_screenwidth()-self.win_w) / 2
        screen_h = (win.winfo_screenheight()-self.win_h) / 2
        
        win.geometry(str(self.win_w)+'x'+str(self.win_h)+'+'+str(screen_w + dx)+'+'+str(screen_h + dy))
    
    def getEndOfMonth(self,month,year):
        num_days = 0
        if month == 4 or month == 6 or month == 9 or month == 11:
            num_days = 30
        elif month == 2:
            if calendar.isleap(year):
                num_days = 29
            else:
                num_days = 28
        else:
            num_days = 31
        return num_days

    def prevMonth(self):
            month = 0
            if datetime.now().month==1:
                month=11
            else:
                month = datetime.now().month - 2
            return month
        
    def prevMonthYear(self,offset):
        year = 0
        if date.month==12:
            year = datetime.now().year + 1
        else:
            year = datetime.now().year
        return year - offset