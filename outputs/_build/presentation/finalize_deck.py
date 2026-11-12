"""Use native PowerPoint to group, animate, save and render the presentation."""
from pathlib import Path
import argparse
import json
import time
import gc
import pythoncom
import win32com.client

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'outputs'
QA=OUT/'_qa'/'presentation'
QA.mkdir(parents=True,exist_ok=True)
PLAN=json.loads((HERE/'animation_plan.json').read_text(encoding='utf-8'))

# Microsoft Office MsoAnimEffect values. Fade/Float/Wipe remain native and editable.
EFFECTS={'fade':10,'float':30,'wipe':22}
MsoAnimTriggerWithPrevious=2
report={'slides':[],'native_powerpoint':True}


def get_collection_item(collection,index):
    return collection.Item(index)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-slides',type=int,nargs='+',default=None,
                        help='Export only these changed slides; always update PPTX, PPSX and PDF.')
    args=parser.parse_args()
    render_slides=args.render_slides or list(range(1,len(PLAN)+1))
    if any(i<1 or i>len(PLAN) for i in render_slides):
        parser.error('Render slide numbers must belong to the presentation.')
    pythoncom.CoInitialize()
    app=None
    presentation=None
    try:
        app=win32com.client.DispatchEx('PowerPoint.Application')
        report['powerpoint_version']=app.Version
        # Open with no document window. Do not alter other user presentations.
        presentation=app.Presentations.Open(str(HERE/'Floodline_Static_Base.pptx'),False,False,False)
        if presentation.Slides.Count!=len(PLAN):
            raise RuntimeError('Slide count differs from the content manifest')
        for item in PLAN:
            slide=presentation.Slides.Item(item['slide'])
            slide.SlideShowTransition.EntryEffect=3849  # ppEffectFadeSmoothly
            slide.SlideShowTransition.Duration=.5
            slide.SlideShowTransition.AdvanceOnTime=False
            slide.SlideShowTransition.AdvanceOnClick=True
            groups=[]
            for g in item['groups']:
                targets=[]
                if len(g['names'])==1:
                    targets=[slide.Shapes.Item(g['names'][0])]
                else:
                    try:
                        names=win32com.client.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_VARIANT,g['names'])
                        grouped=slide.Shapes.Range(names).Group()
                        grouped.Name=f"{item['slide']:02d}_{g['key']}"
                        targets=[grouped]
                    except Exception as exc:
                        # Charts and other Office objects can refuse grouping.
                        targets=[slide.Shapes.Item(n) for n in g['names']]
                        groups.append({'group':g['key'],'grouping_fallback':str(exc)})
                for target in targets:
                    effect=slide.TimeLine.MainSequence.AddEffect(target,EFFECTS[g['effect']],0,MsoAnimTriggerWithPrevious)
                    effect.Timing.Duration=g['duration']
                    effect.Timing.TriggerDelayTime=g['delay']
                    effect.Timing.Accelerate=0
                    effect.Timing.Decelerate=.7 if g['effect']=='float' else 0
                    effect.Timing.AutoReverse=False
                    if g['effect']=='wipe':
                        effect.EffectParameters.Direction=4  # from left
                    groups.append({'name':target.Name,'effect_type':effect.EffectType,'duration':effect.Timing.Duration,'delay':effect.Timing.TriggerDelayTime,'trigger':effect.Timing.TriggerType})
            report['slides'].append({'slide':item['slide'],'title':item['title'],'transition':slide.SlideShowTransition.EntryEffect,'duration':slide.SlideShowTransition.Duration,'animation_count':slide.TimeLine.MainSequence.Count,'animations':groups})
            print(f"Animated slide {item['slide']:02d}: {slide.TimeLine.MainSequence.Count} native effects",flush=True)
        presentation.SaveAs(str(OUT/'Floodline_CAA_Presentation.pptx'),24)
        # PowerPoint itself renders the exact fonts, transparency and native chart.
        presentation.SaveAs(str(OUT/'Floodline_CAA_Presentation.pdf'),32)
        for i in render_slides:
            slide=presentation.Slides.Item(i)
            slide.Export(str(QA/f'slide-{i:02d}.png'),'PNG',1920,1080)
        presentation.SaveCopyAs(str(OUT/'Floodline_CAA_Slideshow.ppsx'),28)
        report['output_pptx']=str(OUT/'Floodline_CAA_Presentation.pptx')
        report['output_pdf']=str(OUT/'Floodline_CAA_Presentation.pdf')
        report['output_show']=str(OUT/'Floodline_CAA_Slideshow.ppsx')
        report['total_native_animations']=sum(s['animation_count'] for s in report['slides'])
        report['rendered_slides']=render_slides
        (QA/'powerpoint_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f"Saved PPTX, PPSX, PDF and {len(render_slides)} full-resolution renders.",flush=True)
    finally:
        if presentation is not None:
            presentation.Close()
        # PowerPoint is a single-instance COM server. Quit only if there are no
        # remaining presentations, so existing user work is never closed.
        if app is not None:
            try:
                if app.Presentations.Count==0:
                    app.Quit()
            except Exception:
                pass
        presentation=None
        app=None
        gc.collect()
        pythoncom.CoUninitialize()


if __name__=='__main__':
    main()
