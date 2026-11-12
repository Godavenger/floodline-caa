"""Read native PowerPoint text bounds and package evidence for presentation QA."""
from pathlib import Path
import json
import re
import zipfile
from itertools import combinations
from lxml import etree
import fitz
import pythoncom
import win32com.client

ROOT=Path(__file__).resolve().parents[3]
PPTX=ROOT/'outputs'/'Floodline_CAA_Presentation.pptx'
QA=ROOT/'outputs'/'_qa'/'presentation'
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}


def descendants(shapes):
    for i in range(1,shapes.Count+1):
        s=shapes.Item(i)
        if s.Type==6:
            yield from descendants(s.GroupItems)
        else:
            yield s


def main():
    report={'text_overflow':[],'text_overlaps':[],'text_boxes':0,'off_slide':[]}
    pythoncom.CoInitialize()
    app=None
    presentation=None
    try:
        app=win32com.client.DispatchEx('PowerPoint.Application')
        presentation=app.Presentations.Open(str(PPTX),True,False,False)
        for i in range(1,presentation.Slides.Count+1):
            sl=presentation.Slides.Item(i)
            rendered_text=[]
            for s in descendants(sl.Shapes):
                if not s.HasTextFrame or not s.TextFrame.HasText:
                    continue
                tr=s.TextFrame.TextRange
                report['text_boxes']+=1
                available_height=s.Height-s.TextFrame.MarginTop-s.TextFrame.MarginBottom
                available_width=s.Width-s.TextFrame.MarginLeft-s.TextFrame.MarginRight
                bh,bw=tr.BoundHeight,tr.BoundWidth
                rendered_text.append({'name':s.Name,'text':tr.Text,
                    'bounds':(tr.BoundLeft,tr.BoundTop,bw,bh)})
                if bh>available_height+1 or bw>available_width+1:
                    report['text_overflow'].append({'slide':i,'name':s.Name,'text':tr.Text,'font':tr.Font.Name,'size':tr.Font.Size,'height':s.Height,'bound_height':bh,'height_excess':round(bh-available_height,2),'width_excess':round(bw-available_width,2)})
                if tr.BoundLeft < 30 or tr.BoundTop < 22 or tr.BoundLeft+bw>presentation.PageSetup.SlideWidth-29 or tr.BoundTop+bh>presentation.PageSetup.SlideHeight-18:
                    report['off_slide'].append({'slide':i,'text':tr.Text,'bounds':[tr.BoundLeft,tr.BoundTop,bw,bh]})
            for first,second in combinations(rendered_text,2):
                x1,y1,w1,h1=first['bounds']
                x2,y2,w2,h2=second['bounds']
                width=min(x1+w1,x2+w2)-max(x1,x2)
                height=min(y1+h1,y2+h2)-max(y1,y2)
                if width>4 and height>1.5:
                    report['text_overlaps'].append({'slide':i,
                        'first':first['name'],'first_text':first['text'],
                        'second':second['name'],'second_text':second['text'],
                        'overlap_points':[round(width,2),round(height,2)]})
        presentation.Close()
        presentation=None
        if app.Presentations.Count==0:
            app.Quit()
    finally:
        if presentation is not None:
            presentation.Close()
        pythoncom.CoUninitialize()
    with zipfile.ZipFile(PPTX) as z:
        slides=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)],key=lambda n:int(re.search(r'(\d+)\.xml',n).group(1)))
        notes=[n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n)]
        charts=[n for n in z.namelist() if re.fullmatch(r'ppt/charts/chart\d+\.xml',n)]
        report.update({'slide_count':len(slides),'speaker_note_count':len(notes),'native_chart_count':len(charts),'animation_slide_count':sum(etree.fromstring(z.read(n)).find('p:timing',NS) is not None for n in slides),'transition_slide_count':sum(etree.fromstring(z.read(n)).find('p:transition',NS) is not None for n in slides)})
        report['placeholder_matches']=[]
        for n in slides:
            t=' '.join(etree.fromstring(z.read(n)).xpath('//a:t/text()',namespaces=NS))
            if re.search(r'\b(lorem|ipsum|TODO|placeholder|To assign|To complete)\b',t,re.I):
                report['placeholder_matches'].append({'slide':n,'text':t})
    pdf=fitz.open(ROOT/'outputs'/'Floodline_CAA_Presentation.pdf')
    report['pdf_pages']=len(pdf)
    (QA/'content_and_fit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({key:len(value) if isinstance(value,list) else value
                     for key,value in report.items()},indent=2))


if __name__=='__main__':
    main()
