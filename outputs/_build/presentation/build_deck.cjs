/* Floodline: editable widescreen glass presentation, with native animation plan. */
const fs = require('fs');
const path = require('path');
const PptxGenJS = require('../presentation_runtime/node_modules/pptxgenjs');
const sharp = require('../presentation_runtime/node_modules/sharp');
const ROOT = path.resolve(__dirname, '../../..');
const React = require(path.join(ROOT, 'frontend/node_modules/react'));
const ReactDOMServer = require(path.join(ROOT, 'frontend/node_modules/react-dom/server'));
const Icons = require(path.join(ROOT, 'frontend/node_modules/lucide-react'));
const ASSET = path.join(__dirname,'assets');
const OUT = path.join(ROOT,'outputs');
const pilot = JSON.parse(fs.readFileSync(path.join(ROOT,'data/fixtures/pilot.json'),'utf8'));
const evaluation = JSON.parse(fs.readFileSync(path.join(OUT,'evidence/evaluation.json'),'utf8'));
const browser = JSON.parse(fs.readFileSync(path.join(OUT,'evidence/browser-acceptance.json'),'utf8'));
const performance = JSON.parse(fs.readFileSync(path.join(OUT,'evidence/performance.json'),'utf8'));

const P={ink:'F2FAF8',muted:'A5BFBE',faint:'799B9D',mint:'79E3C8',teal:'4FA7A2',coral:'EEA393',amber:'EDCD86',bg:'07171D',line:'6E9694'};
const pptx=new PptxGenJS();
pptx.layout='LAYOUT_WIDE';
pptx.author='Floodline CAA Project';
pptx.subject='Smart City Flood Prediction and Community Alert Platform — synthetic pilot';
pptx.title='Floodline | CAA Project Presentation';
pptx.company='CAA Project';
pptx.lang='en-IN';
pptx.theme={headFontFace:'Arial',bodyFontFace:'Arial',lang:'en-IN'};
const S=pptx.ShapeType;
const W=13.333333, H=7.5, M=.65;
let counter=0, currentGroup=null, currentSlide=null;
const animationPlan=[];
const contentManifest=[];
const layoutManifest=[];
const icons={};

function named(opts,type){
  const objectName=`s${String(currentSlide._index).padStart(2,'0')}_${currentGroup ? currentGroup.key : 'static'}_${type}_${counter++}`;
  if(currentGroup)currentGroup.names.push(objectName);
  layoutManifest.push({slide:currentSlide._index,name:objectName,type,x:opts.x,y:opts.y,w:opts.w,h:opts.h,fontSize:opts.fontSize,text:opts._text});
  return {...opts,objectName};
}
function text(value,x,y,w,h,size=18,opts={}){
  // Office's Arial line height is about 1.2 times its point size. Include
  // that descent space without changing the text's top-aligned position.
  const lines=typeof value==='string' ? value.split(/\r?\n/).length : 1;
  h=Math.max(h,lines*size*1.25/72);
  const n=named({x,y,w,h,fontFace:'Arial',fontSize:size,color:P.ink,margin:0,breakLine:false,valign:'top',paraSpaceAfterPt:0,...opts,_text:typeof value==='string'?value:JSON.stringify(value)},'text');
  delete n._text;
  currentSlide.addText(value,n);
}
function shape(type,x,y,w,h,opts={}){currentSlide.addShape(type,named({x,y,w,h,...opts},'shape'));}
function panel(x,y,w,h,opts={}){
  shape(S.roundRect,x,y,w,h,{rectRadius:.20,radius:.2,fill:{color:'D8F8EE',transparency:94},line:{color:'BFEBE0',transparency:77,width:.8},shadow:{type:'outer',color:'000C10',blur:15,angle:90,offset:3,opacity:.19},...opts});
}
function line(x1,y1,x2,y2,color=P.line,width=1.2,opts={}){
  const x=Math.min(x1,x2),y=Math.min(y1,y2);
  shape(S.line,x,y,Math.abs(x2-x1),Math.abs(y2-y1),{flipH:x2<x1,flipV:y2<y1,line:{color,width,...opts}});
}
function arrow(x1,y1,x2,y2,color=P.mint,width=1.7){line(x1,y1,x2,y2,color,width,{beginArrowType:'none',endArrowType:'triangle'});}
function dot(x,y,r=.045,color=P.mint,opts={}){shape(S.ellipse,x-r,y-r,r*2,r*2,{fill:{color},line:{color,transparency:100},...opts});}
function pill(value,x,y,w,color=P.mint,opts={}){
  shape(S.roundRect,x,y,w,.34,{radius:.15,rectRadius:.15,fill:{color,transparency:88},line:{color,transparency:78,width:.7}});
  text(value,x+.12,y+.065,w-.24,.20,10.1,{color,bold:true,...opts});
}
function image(name,x,y,w,h,opts={}){currentSlide.addImage(named({path:path.join(ASSET,`${name}.png`),x,y,w,h,...opts},'image'));}
function icon(name,x,y,size=.36,color='mint'){
  currentSlide.addImage(named({path:icons[`${name}-${color}`],x,y,w:size,h:size,altText:name},'icon'));
}
function group(key,delay,fn,effect='fade',duration=.45){
  const prior=currentGroup;
  const g={key,names:[],delay,effect,duration};currentGroup=g;fn();currentGroup=prior;
  if(g.names.length)animationPlan[currentSlide._index-1].groups.push(g);
}
function header(section,title,subtitle='',bg='background'){
  const sl=pptx.addSlide();currentSlide=sl;sl._index=animationPlan.length+1;
  counter=0;sl.background={color:P.bg};
  animationPlan.push({slide:sl._index,title,transition:'fade',groups:[]});
  sl.addImage({path:path.join(ASSET,`${bg}.jpg`),x:0,y:0,w:W,h:H,objectName:`background_${sl._index}`});
  group('heading',0,()=>{
    text(section.toUpperCase(),M,.43,11.7,.19,10.1,{bold:true,charSpacing:2.3,color:P.mint});
    text(title,M,.86,12.03,.64,36,{bold:true,charSpacing:-.8});
    if(subtitle)text(subtitle,M,1.57,11.85,.46,16.4,{color:P.muted});
  },'fade',.4);
  text('FLOODLINE  /  CAA PROJECT',M,7.08,5,.16,9.2,{color:P.faint,charSpacing:1.2});
  text(`${String(sl._index).padStart(2,'0')}  /  20`,11.67,7.08,1.03,.18,9.2,{align:'right',color:P.faint});
  return sl;
}
function notes(summary,script,sources,duration='40 seconds'){
  const title=animationPlan[currentSlide._index-1].title;
  const value=`${title}\nSuggested speaking time: ${duration}.\n\nMAIN POINT\n${summary}\n\nPRESENTER SCRIPT\n${script}\n\nANIMATION\nThe title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.\n\nSOURCES\n${sources}\n\nSCOPE\nThis release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.`;
  currentSlide.addNotes(value);
  contentManifest.push({slide:currentSlide._index,title,summary,script,sources,duration});
}
function stat(value,label,x,y,w=2.5,color=P.mint){
  text(value,x,y,w,.76,49,{bold:true,color,charSpacing:-1.1});
  text(label,x,y+.86,w,.55,16.5,{color:P.muted});
}
function miniCard(name,title,body,x,y,w,h=1.55,color='mint'){
  panel(x,y,w,h);icon(name,x+.23,y+.25,.37,color);
  const titleLines=title.split('\n').length;
  const bodyTop=titleLines>1 ? 1.09 : .83;
  text(title,x+.76,y+.26,w-1,.35,18.3,{bold:true});
  text(body,x+.24,y+bodyTop,w-.48,h-bodyTop-.15,16.3,{color:P.muted});
}
const riskColors={A1:P.teal,A2:P.teal,A3:P.teal,B1:P.teal,B2:P.teal,B3:P.amber,C1:P.coral,C2:P.coral,C3:'7B9294'};

function mapDiagram(x,y,w,h,options={}){
  // The supplied WGS84 geometry, rendered as editable PowerPoint shapes.
  const [south,west]=pilot.bounds[0], [north,east]=pilot.bounds[1];
  const px=(lon)=>x+(lon-west)/(east-west)*w;
  const py=(lat)=>y+h-(lat-south)/(north-south)*h;
  if(options.cells!==false){
    for(const a of pilot.areas){
      const c=a.geometry.coordinates[0];
      const left=px(Math.min(...c.map(p=>p[0]))),right=px(Math.max(...c.map(p=>p[0])));
      const top=py(Math.max(...c.map(p=>p[1]))),bottom=py(Math.min(...c.map(p=>p[1])));
      shape(S.rect,left+.024,top+.024,right-left-.048,bottom-top-.048,{fill:{color:riskColors[a.id],transparency:options.cellTransparency ?? 77},line:{color:'B5E6D9',transparency:84,width:.8}});
      if(options.labels)text(a.id,left+.12,top+.10,right-left-.20,.24,12.2,{bold:true,color:a.id==='C3'?'B7C9C8':P.ink});
      if(a.id==='C3' && options.hatch){for(let z=0;z<7;z++){const xx=left+.1+z*(right-left-.2)/7;line(xx,top+.14,Math.min(xx+.32,right-.06),bottom-.12,'95ADAE',.55,{transparency:40});}}
    }
  }
  if(options.roads!==false){
    const seen=new Set();
    for(const r of pilot.roads){
      if(seen.has(r.segment_id))continue;seen.add(r.segment_id);
      const c=r.geometry.coordinates;
      for(let k=0;k<c.length-1;k++)line(px(c[k][0]),py(c[k][1]),px(c[k+1][0]),py(c[k+1][1]),'6B9493',1.05,{transparency:options.roadTransparency ?? 34});
    }
  }
  // The actual fixture river is a display layer, separate from the road graph.
  const river=[ [88.357,22.592],[88.355,22.579],[88.3575,22.569],[88.356,22.557] ];
  for(let k=0;k<river.length-1;k++)line(px(river[k][0]),py(river[k][1]),px(river[k+1][0]),py(river[k+1][1]),'70BCB9',5.5,{transparency:43});
  if(options.excluded){
    const seen=new Set();
    for(const id of options.excluded){const r=pilot.roads.find(r=>r.id===id);if(!r||seen.has(r.segment_id))continue;seen.add(r.segment_id);const c=r.geometry.coordinates;for(let k=0;k<c.length-1;k++)line(px(c[k][0]),py(c[k][1]),px(c[k+1][0]),py(c[k+1][1]),P.coral,4,{dashType:'dash'});}
  }
  if(options.route){
    for(const id of options.route){const r=pilot.roads.find(r=>r.id===id);if(!r)throw new Error(`Missing route edge ${id}`);const c=r.geometry.coordinates;for(let k=0;k<c.length-1;k++)line(px(c[k][0]),py(c[k][1]),px(c[k+1][0]),py(c[k+1][1]),P.mint,3.3);}
  }
  if(options.nodes){for(const n of pilot.nodes){dot(px(n.longitude),py(n.latitude),.031,P.muted);}}
  if(options.endpoints){
    const start=pilot.nodes.find(n=>n.id==='n0-1'),end=pilot.nodes.find(n=>n.id==='n4-1');
    for(const [n,label] of [[start,'Library'],[end,'Station']]){
      dot(px(n.longitude),py(n.latitude),.07,P.mint);
      text(label,px(n.longitude)-.41,py(n.latitude)+.16,.90,.23,11.8,{bold:true,align:'center'});
    }
  }
}

async function prepareIcons(){
  const names=['CloudRain','Map','MapPinned','Layers','ShieldCheck','Route','Bell','Database','LockKeyhole','Activity','CircleHelp','Clock3','GitBranch','CheckCheck','Upload','CircleCheck','CloudOff','Eye','Users','SlidersHorizontal','FileCheck2','ArrowUpRight','BookOpen','Globe','Droplets','Building2','Compass','RefreshCw','TriangleAlert','Gauge','Waypoints','TimerReset','FileText','Check','Network','CodeXml'];
  for(const name of names){
    for(const [key,color] of [['mint',P.mint],['coral',P.coral],['amber',P.amber],['muted',P.muted]]){
      const component=Icons[name];if(!component)throw new Error(`No icon ${name}`);
      const svg=ReactDOMServer.renderToStaticMarkup(React.createElement(component,{color:'#'+color,size:256,strokeWidth:1.7}));
      const dest=path.join(ASSET,`icon-${name}-${key}.png`);
      await sharp(Buffer.from(svg)).resize(256,256).png().toFile(dest);icons[`${name}-${key}`]=dest;
    }
  }
}

async function build(){
  await prepareIcons();

  // 01 — Cover: original, editable glass cartography and floating evidence.
  header('CAA project presentation','', '', 'hero');
  animationPlan[0].title='Floodline — From rainfall to local decisions';
  group('cover_wordmark',.03,()=>{
    icon('Layers',.68,1.03,.42);
    text('FLOODLINE',1.27,1.02,6.55,.72,49,{bold:true,charSpacing:1.0});
    text('From rainfall\nto local decisions.',.66,2.25,7.25,1.73,42,{bold:true,charSpacing:-1.1,breakLine:false});
    text('Smart City Flood Prediction\n& Community Alert Platform',.69,4.34,6.55,.89,21,{color:P.muted,breakLine:false});
    pill('SYNTHETIC PILOT  /  v0.1.1',.70,5.73,3.20);
    text('12 November 2026',.71,6.32,4.95,.26,14.4,{color:P.muted});
  },'float',.5);
  group('cover_map',.18,()=>{
    panel(8.19,2.24,4.34,3.69,{fill:{color:'C7F5E7',transparency:92}});
    mapDiagram(8.45,2.56,3.75,2.90,{labels:true,hatch:true,cellTransparency:70});
    text('INVENTED GEOGRAPHY  /  3 WARDS',8.49,5.56,3.49,.18,9.2,{charSpacing:1.2,color:P.muted});
  },'float',.55);
  group('cover_context',.40,()=>{
    panel(9.32,1.45,3.00,.99);icon('MapPinned',9.54,1.72,.35);
    text('9 analysis cells',10.07,1.68,2.00,.28,18.5,{bold:true});
    text('Evidence at area level',10.07,2.05,2.00,.18,10.8,{color:P.muted});
    panel(7.75,5.53,3.84,1.07);icon('ShieldCheck',7.98,5.84,.40);
    text('Review before action',8.55,5.80,2.78,.30,18.2,{bold:true});
    text('Reports → verified road evidence',8.55,6.19,2.78,.18,10.4,{color:P.muted});
  },'float',.55);
  notes('Floodline connects environmental context and reviewed community observations to understandable local actions.',
    'Introduce the project with its full assignment title. Floodline is the project name. Say early that this is a working synthetic pilot: the wards, rainfall, gauges and roads are development fixtures. We will show the data-to-action pipeline, the working interface, recorded checks, and the evidence required for a real pilot. Do not describe the displayed index as a probability.',
    'project description.docx, item 3; PRODUCT.md; docs/PROJECT_REPORT.md; docs/PROJECT_STATUS.md.','30 seconds');

  // 02 — The assignment problem expressed as three concrete decisions.
  header('The problem','Limited data has to become a useful local decision.',
    'Residents and municipal reviewers need location, evidence and a supported next step.');
  const questions=[
    ['01','MapPinned','Where is it vulnerable?','Rainfall, terrain and drainage need a shared geographic context.'],
    ['02','Eye','What has been observed?','A report needs a time, a location and a reviewable account of conditions.'],
    ['03','Route','Which action is supported?','Warnings and routes must reflect current, verified evidence.'],
  ];
  questions.forEach((q,i)=>group(`question_${i}`,.14+i*.16,()=>{
    const x=M+i*4.11;panel(x,2.39,3.81,3.49);
    text(q[0],x+.25,2.61,1.05,.80,56,{bold:true,color:P.teal,charSpacing:-1.9});
    icon(q[1],x+2.99,2.74,.48);
    text(q[2],x+.26,3.80,3.23,.82,23.1,{bold:true});
    text(q[3],x+.26,4.71,3.19,.89,17.2,{color:P.muted});
  },'float'));
  group('problem_takeaway',.67,()=>text('Floodline brings these decisions into one traceable workflow.',M,6.37,11.6,.34,21,{color:P.mint}));
  notes('The assignment challenge is turning limited environmental data into timely, understandable information.',
    'Frame the problem through these three questions. A rainfall value alone cannot establish water on a particular street. A community report alone is not yet a verified road closure. The platform gives environmental evidence and reported conditions their own review paths, then joins them in an understandable map and action workflow. The disciplines are computer science, geography, civil engineering, meteorology and disaster management.',
    'project description.docx, item 3; PRODUCT.md; docs/PROJECT_REPORT.md.');

  // 03 — Two distinct streams, joining in a shared map.
  header('System concept','One platform. Two evidence streams.',
    'Environmental warnings and observed road conditions keep their own meanings.');
  group('environmental',.14,()=>{
    panel(.66,2.32,4.48,1.61);icon('CloudRain',.92,2.57,.46);
    text('Environmental evidence',1.60,2.61,3.20,.32,18,{bold:true});
    text('Rainfall + geographic features\n→ interpretable warning rule',.95,3.20,3.83,.49,17.2,{color:P.muted});
  },'float');
  group('community',.30,()=>{
    panel(.66,4.40,4.48,1.61);icon('ShieldCheck',.92,4.66,.46);
    text('Community observations',1.60,4.68,3.20,.32,18,{bold:true});
    text('Private report + moderator review\n→ current road-edge hazard',.95,5.27,3.86,.49,17.2,{color:P.muted});
  },'float');
  group('joining',.47,()=>{arrow(5.22,3.12,6.32,3.92);arrow(5.22,5.18,6.32,4.24);},'wipe',.40);
  group('map_output',.58,()=>{
    panel(6.43,3.00,2.52,2.50);icon('Map',7.26,3.32,.61);
    text('Shared map',6.68,4.13,2.06,.36,23,{bold:true,align:'center'});
    text('Source • time • support',6.68,4.79,2.06,.24,12.2,{color:P.muted,align:'center'});
  },'float');
  group('actions',.75,()=>{
    arrow(9.07,4.23,9.72,4.23);
    miniCard('Bell','Ward alerts','Consent-based\nin-app delivery',9.88,2.70,2.78,1.84);
    miniCard('Route','Route\nsuggestions','Exclude active\nverified road hazards',9.88,4.92,2.78,1.84);
  });
  notes('Environmental risk context and moderator-verified road hazards are separate action streams.',
    'Walk left to right as the diagram builds. The environmental stream validates observations and combines recent rain with synthetic static susceptibility. The community stream keeps pending observations private and requires authenticated review before creating a bounded road restriction. Both streams appear in the map with source and validity information. Alerts use consent and a persistent delivery lifecycle. Routes exclude active verified edges; a coarse risk cell does not automatically close roads. Community reports do not automatically become model training labels.',
    'docs/ARCHITECTURE.md; docs/API_CONTRACTS.md; docs/MODEL_CARD.md.','45 seconds');

  // 04 — Real screenshot, without tiny explanatory text overlaid on the image.
  header('Working prototype','The map is the starting point.',
    'A real capture of the delivered interface, with ward evidence beside the geography.');
  group('actual_dashboard',.16,()=>{
    panel(.66,2.24,8.59,4.65);image('dashboard',.80,2.39,8.30,4.36);
  },'float');
  group('dashboard_stats',.39,()=>{
    stat('3','synthetic wards',9.76,2.40,2.75);
    stat('9','analysis cells',9.76,4.01,2.75);
    stat('61','directed road edges',9.76,5.62,2.75);
  });
  notes('The application leads with a map and evidence, rather than hiding the data behind a single score.',
    'Point out the map, the warning summary, the selected area and source-support panel. In the recorded initial state, three of the eight evaluated cells meet the warning rule and one cell is unknown. The geometry is invented, although its display uses WGS84 coordinates. The interface has resident reporting, routing, alerts, data/model details and moderator review. Light, Dark and System appearance are implemented. The screenshot is from the accepted dark-mode workflow and is a backup if the live demonstration is unavailable.',
    '.impeccable/review/desktop-dark.png; docs/ACCEPTANCE.md; data/fixtures/pilot.json.','35 seconds');

  // 05 — Quality outcomes and a receipt-time explanation.
  header('Data engineering','Raw data becomes traceable evidence.',
    'Checksums, explicit units and receipt-time availability make the input reproducible.','data');
  group('ingestion_totals',.13,()=>{
    panel(.66,2.30,4.19,3.72);icon('Database',.93,2.61,.45);
    text('869 raw records',1.58,2.67,2.93,.35,23,{bold:true});
    stat('866','accepted observations',.96,3.47,3.49);
    pill('1 DUPLICATE',.96,5.24,1.75,P.muted);pill('2 QUARANTINED',2.89,5.24,1.67,P.coral);
  },'float');
  group('data_flow',.29,()=>{
    miniCard('FileCheck2','Validate','Units, ranges, timestamps\nand provenance',5.28,2.30,3.43,1.65);
    miniCard('GitBranch','Preserve reasons','Invalid records enter\na quarantine ledger',9.09,2.30,3.55,1.65,'coral');
  });
  group('receipt_timeline',.47,()=>{
    panel(5.28,4.39,7.36,1.63);
    text('What was available at issue time?',5.56,4.63,6.70,.30,20,{bold:true});
    line(5.93,5.26,11.94,5.26,'709B99',1.4);
    [[6.03,'Observed',P.muted],[8.93,'Issued',P.mint],[11.84,'Received late',P.coral]].forEach(([x,t,c])=>{dot(x,5.26,.07,c);text(t,x-.77,5.53,1.58,.24,12.5,{align:'center',color:c,bold:true});});
    text('This late record is excluded from the earlier snapshot.',5.58,6.43,6.90,.27,17.6,{color:P.mint});
  },'wipe',.5);
  notes('Quality checks and receipt time prevent invalid inputs and temporal leakage.',
    'The initial raw archive has 869 records: 866 accepted, one exact duplicate ignored, and two invalid records quarantined with reasons. SHA-256 manifests freeze the fixture inputs. Units are converted explicitly. Explain the timeline: a reading may have an earlier observation timestamp but arrive after a warning was issued, so it cannot be used in that earlier feature snapshot. Missing intervals remain missing; absence does not become zero rainfall.',
    'docs/PROJECT_REPORT.md, Data and GIS; docs/DATA_DICTIONARY.md; data/manifest.json; outputs/evidence/backend-acceptance.json.');

  // 06 — Editable geography built from the project fixture.
  header('Geographic reasoning','GIS connects area context to a directed road graph.',
    'The illustration uses the supplied synthetic geometry and road connections.');
  group('gis_map',.16,()=>{
    panel(.66,2.28,7.00,4.60);
    mapDiagram(1.03,2.59,5.98,3.69,{labels:true,hatch:true,nodes:true,cellTransparency:80});
    text('WESTBANK',1.14,6.51,1.79,.20,10.2,{bold:true,color:P.muted,charSpacing:.8});
    text('MARKET WARD',3.23,6.51,1.87,.20,10.2,{bold:true,color:P.muted,charSpacing:.8});
    text('EASTBANK',5.38,6.51,1.76,.20,10.2,{bold:true,color:P.muted,charSpacing:.8});
  },'float');
  group('gis_facts',.37,()=>{
    miniCard('Layers','9 analysis cells','Approximately 1 km spatial support',8.02,2.30,4.60,1.50);
    miniCard('Waypoints','21 nodes / 61 directed edges','One-way and disconnected\ncases included',8.02,4.02,4.60,1.50);
    text('WGS84 for display\nUTM 45N for distances',8.27,5.73,4.13,.64,20,{bold:true});
    text('Area susceptibility and road-water depth require different evidence.',8.27,6.54,4.12,.44,12.2,{color:P.muted});
  });
  notes('GIS keeps map display, distance calculation and road restrictions at the appropriate spatial scales.',
    'Explain the nine approximately one-kilometre cells and the directed road graph of 21 nodes and 61 edges. Display coordinates are WGS84, but distances and spatial matching are projected to EPSG:32645, UTM zone 45N. The test fixture includes one-way and disconnected routes. A kilometre-scale warning cell cannot determine water depth on a street. Road exclusions require reviewed evidence matched to a particular edge. The colored cells reproduce the recorded initial-state schematic, and all geography remains synthetic.',
    'data/fixtures/pilot.json; docs/ARCHITECTURE.md; docs/PROJECT_REPORT.md; backend/floodline/geo.py.');

  // 07 — Exact active rule, with no probability language.
  header('Active baseline','An interpretable rule runs the demo.',
    'The current index combines static susceptibility with recent rainfall.','data');
  group('active_equation',.17,()=>{
    panel(.66,2.34,11.99,1.37);
    text('INDEX',.99,2.73,1.49,.33,21,{bold:true,color:P.muted});
    text('=',2.47,2.57,.56,.61,36,{bold:true});
    text('0.35 S',3.25,2.51,3.20,.70,45,{bold:true,color:P.mint});
    text('+',6.77,2.57,.58,.61,36,{bold:true,color:P.muted});
    text('0.65 R',7.70,2.51,3.88,.70,45,{bold:true,color:P.mint});
    text('Rounded relative warning index',3.25,3.30,8.28,.18,11.7,{color:P.muted});
  },'float');
  group('rule_features',.34,()=>{
    miniCard('Building2','S: static susceptibility','Imperviousness, drainage, relative\nelevation and distance to water',.66,4.13,5.82,1.58);
    miniCard('CloudRain','R: recent rainfall','Three-hour rainfall scaled to\n75 mm, capped at 100',6.83,4.13,5.82,1.58);
  });
  group('risk_thresholds',.52,()=>{
    const items=[['MONITOR','Index < 55',P.mint],['ELEVATED','55–74',P.amber],['HIGH','≥ 75',P.coral],['UNKNOWN','Missing / stale rain',P.muted]];
    items.forEach((q,i)=>{const x=.68+i*3.06;pill(q[0],x,6.15,2.72,q[2]);text(q[1],x+.12,6.64,2.71,.23,14,{color:P.muted});});
  });
  notes('The active service uses a transparent threshold rule, not the unpromoted logistic model.',
    'The active version is demo-threshold-v1. Static susceptibility S equals 100 times 0.35 times impervious fraction, plus 0.35 times drainage constraint, plus 0.20 times max(0,1-relative elevation/10), plus 0.10 times max(0,1-distance to water/1500), rounded. R is min(100, rainfall in three hours / 75 times 100). The current index is round(0.35 S + 0.65 R). High begins at 75, Elevated at 55, otherwise Monitor. Missing rainfall, rain older than 90 minutes, or under 75 percent expected interval coverage gives Unknown with a null index. Gauge values are contextual and affect support flags, not this numeric index. All weights and thresholds are demo assumptions. The three-hour validity limit is a record lifetime, not an established forecasting horizon.',
    'docs/MODEL_CARD.md, Active rule; backend/floodline/prediction.py.','45 seconds');

  // 08 — Screenshot map with a legible native evidence card.
  header('Resident experience','The evidence is visible beside the map.',
    'Risk words, timestamps and support flags help a resident interpret the display.');
  group('evidence_map',.16,()=>{
    panel(.66,2.28,7.24,4.58);image('dashboard_map',.79,2.44,6.98,4.28);
  },'float');
  group('native_evidence',.39,()=>{
    panel(8.27,2.28,4.37,4.58);
    text('EASTBANK · CENTRAL',8.57,2.57,3.74,.23,11.3,{charSpacing:1.1,color:P.muted,bold:true});
    pill('HIGH  /  DEMO RULE',8.57,3.09,2.38,P.coral);
    text('81',8.53,3.67,2.09,.97,64,{bold:true,charSpacing:-2,color:P.ink});
    text('/ 100',10.79,4.03,1.45,.30,20,{color:P.muted});
    text('64.8 mm rain / past 3 hours',8.58,4.99,3.75,.27,17.2,{bold:true});
    text('Observed 14:00 IST  •  support: Limited',8.58,5.48,3.69,.42,13.7,{color:P.muted});
    text('Relative index; no calibrated probability.',8.58,6.29,3.65,.33,13.5,{color:P.mint});
  },'float');
  notes('The interface separates the warning index from the quality and time support of its evidence.',
    'This native summary reproduces the selected C2 area in the captured dashboard: High, index 81 out of 100, 64.8 millimetres known rainfall in the past three hours, observed at 14:00 IST, and Limited support. The source panel also shows a stale synthetic gauge reading of 5.2 metres with an arbitrary datum. Explain that a large index does not mean an 81 percent flood probability. Unknown cells remain visibly different and appear in the summary denominator. The accessible interface uses words as well as color, a text alternative to map-only information, and keyboard focus.',
    '.impeccable/review/desktop-dark.png; docs/MODEL_CARD.md; docs/ACCEPTANCE.md.','35 seconds');

  // 09 — Community privacy and authenticated moderation.
  header('Community reporting','Reports earn trust through review.',
    'An observation stays private while its time, location and publication permissions are checked.');
  group('resident_report',.16,()=>{
    panel(.66,2.31,4.09,4.57);
    pill('RESIDENT / SUBMIT',.91,2.54,2.30);
    image('report_form',.92,3.10,2.36,2.88);
    text('Image +\nlocation +\nobserved time',3.49,3.55,1.02,1.02,13.2,{bold:true});
    text('Pending reports and images\nremain private.',.92,6.30,3.55,.55,15.5,{color:P.muted});
  },'float');
  group('review_bridge',.38,()=>arrow(4.89,4.63,5.49,4.63),'wipe',.4);
  group('moderation_review',.46,()=>{
    panel(5.66,2.31,6.98,4.57);
    pill('MODERATOR / VERIFY',5.94,2.54,2.63);
    image('moderation',5.94,3.12,6.42,2.91);
    text('Authenticated review → bounded road hazard',5.95,6.29,6.29,.32,18.1,{bold:true,color:P.mint});
  },'float');
  notes('Reports become actionable only after authenticated and documented review.',
    'A resident supplies observed conditions, a location pin or coordinates, time, optional image, and publication permissions. Pending reports and images belong to the resident session and are private. Uploads are size and content validated, oriented, stripped of EXIF metadata, and re-encoded. A moderator checks time and location, records a reason, matches evidence to an appropriate road segment, and confirms privacy handling before verification. Publication is a separate explicit choice. Verified current restrictions can then affect routes and alerts. An unreviewed report cannot block a road. Do not invent human testing or field verification; these are software workflow demonstrations.',
    '.impeccable/review/report-form-dark.png; .impeccable/review/moderation-dark.png; docs/API_CONTRACTS.md; docs/ACCEPTANCE.md.','40 seconds');

  // 10 — Two editable, accurate routes from the browser evidence.
  header('Verified hazard routing','Reviewed evidence changes the route.',
    'The recorded Library → Station comparison excludes a newly verified segment.');
  group('route_before',.16,()=>{
    panel(.66,2.29,5.82,3.76);pill('BEFORE / 1 ACTIVE HAZARD',.91,2.51,3.02);
    mapDiagram(1.01,3.00,5.10,2.58,{route:browser.route_comparison.before.edge_ids,excluded:['road-n2-1-n3-1'],endpoints:true,cellTransparency:95,roads:true});
  },'float');
  group('route_after',.38,()=>{
    panel(6.83,2.29,5.82,3.76);pill('AFTER / 2 ACTIVE HAZARDS',7.08,2.51,3.04,P.coral);
    mapDiagram(7.18,3.00,5.10,2.58,{route:browser.route_comparison.after.edge_ids,excluded:browser.route_comparison.after.excluded_edge_ids,endpoints:true,cellTransparency:95,roads:true});
  },'float');
  group('route_conclusion',.58,()=>{
    text('Different edges. Same 4.445 km.',.91,6.40,6.81,.37,23.3,{bold:true,color:P.mint});
    text('The synthetic graph contains tied paths.\nOnly current, verified edge hazards are excluded.',8.01,6.37,4.44,.46,14.2,{color:P.muted});
  });
  notes('The route behavior is demonstrated with different edges, without claiming a shorter or universally safe path.',
    'Both recorded routes are 4444.9 metres long because the fixture has tied alternatives. Initially the route follows the north approach to Station. After verification, both directions of that approach are excluded along with the already-active hazard. The recalculated route uses different edges. The diagrams are editable renderings of the exact before/after edge IDs in browser-acceptance.json. The service handles one-way rules and unreachable destinations. A route avoids currently verified hazards on the mapped graph; other unreported hazards and original-pin connectors may still exist.',
    'outputs/evidence/browser-acceptance.json, route_comparison; data/fixtures/pilot.json; .impeccable/review/route-before-dark.png; .impeccable/review/route-after-dark.png.','40 seconds');

  // 11 — Alert lifecycle with an actual recorded interface.
  header('Consent and delivery','Alerts remember consent, retries and expiry.',
    'Persistent decisions prevent repeated processing from becoming repeated messages.');
  group('alert_capture',.16,()=>{
    panel(.66,2.31,6.08,4.55);image('alerts',.81,2.47,5.78,4.18);
  },'float');
  const lifecycle=[
    ['Bell','Opt in to a ward','A resident chooses subscriptions.'],
    ['CheckCheck','Deduplicate the trigger','Unchanged reminders use a\n30-minute cooldown.'],
    ['TimerReset','Bound delivery attempts','Retries after 30 and 60 seconds;\n3 attempts maximum.'],
    ['Clock3','Cancel stale actions','Withdrawal, expiry and resolved\nhazards stop delivery.'],
  ];
  lifecycle.forEach((q,i)=>group(`alert_step_${i}`,.32+i*.12,()=>{
    const y=2.36+i*1.12;icon(q[0],7.17,y+.09,.38);
    text(q[1],7.83,y+.04,4.73,.29,19.1,{bold:true});
    text(q[2],7.83,y+.46,4.71,.42,15.6,{color:P.muted});
  }));
  notes('The notification lifecycle is implemented and tested, using a simulated in-app adapter.',
    'Residents must opt in to a ward. Persistent idempotency prevents duplicate deliveries for the same trigger. A 30-minute cooldown applies to unchanged warning reminders, while severity escalation may bypass it. A simulated failed attempt retries after 30 seconds, then after 60 seconds, with three attempts in total. Withdrawn consent, stale or superseded evidence, resolved hazards and expiry stop queued delivery. These are in-app simulation records; no real email or SMS is sent. The captured interface is the actual delivery-history screen.',
    'docs/DEMO_RUNBOOK.md, Replay controls and delivery; docs/ACCEPTANCE.md; .impeccable/review/alerts-active-dark.png.');

  // 12 — Chronological storm split, editable and proportionate.
  header('Software experiment','Synthetic evaluation keeps events separate.',
    '18 invented storms supply 624 usable rows; later storms remain held out.','data');
  const splits=[
    ['TRAIN','10', 'events / 345 rows', 'Fit preprocessing',6.27,P.mint],
    ['VALIDATE','4','events / 141 rows','Select F₂ threshold',2.51,P.amber],
    ['TEST','4','events / 138 rows','Freeze comparison',2.51,P.coral],
  ];
  let splitX=.66;
  splits.forEach((q,i)=>{const x=splitX;splitX+=q[4]+.34;group(`split_${i}`,.15+i*.19,()=>{
    panel(x,2.45,q[4],3.28,{fill:{color:q[5],transparency:94}});
    text(q[0],x+.26,2.74,q[4]-.52,.23,12,{bold:true,charSpacing:1.4,color:q[5]});
    text(q[1],x+.22,3.31,q[4]-.46,1.02,71,{bold:true,color:q[5],charSpacing:-2});
    text(q[2],x+.26,4.63,q[4]-.52,.46,17.1,{color:P.muted});
    text(q[3],x+.26,5.19,q[4]-.52,.27,14.5,{bold:true});
  },'float');});
  group('temporal_rule',.75,()=>{
    icon('GitBranch',.87,6.24,.43);
    text('Earlier events → later events. No row substitutes for an independent storm.',1.54,6.28,10.93,.32,20,{color:P.mint});
  });
  notes('The logistic candidate is a separate software experiment with chronological event-level splits.',
    `There are ${evaluation.independent_events} synthetic storms and ${evaluation.usable_rows} usable rows. Twenty-four unknown-label rows are excluded. Ten training events produce 345 rows, four validation events 141 rows, and four final-test events 138 rows. Positive onset times fall after issue time within the three-hour target window. Imputation, missing indicators, scaling and class weighting are fitted on training only. Validation F2 selects a threshold of 0.3, which is frozen before the final test. Storm groups are separated chronologically, and target/look-back overlaps are purged as whole groups if present. This dataset has no real historical validation.`,
    'outputs/evidence/evaluation.json; outputs/evidence/split-manifest.json; docs/MODEL_CARD.md.');

  // 13 — Native PowerPoint chart, with the actual tradeoff foregrounded.
  header('Evaluation result','Higher recall brought more false positives.',
    'Held-out synthetic rows compare the logistic candidate with a rainfall-only baseline.','data');
  group('metric_panel',.13,()=>panel(.66,2.25,7.65,4.02));
  group('metric_chart',.28,()=>{
    currentSlide.addChart(pptx.ChartType.bar,[
      {name:'Logistic candidate',labels:['Recall','Precision'],values:[100,71.01]},
      {name:'Rainfall-only',labels:['Recall','Precision'],values:[87.76,91.49]},
    ],named({
      x:.93,y:2.57,w:7.04,h:3.26,barDir:'col',barGrouping:'clustered',
      showTitle:true,title:'Held-out synthetic comparison',titleFontFace:'Arial',titleFontSize:15,titleColor:P.muted,
      chartColors:[P.mint,P.amber],showValue:true,dataLabelPosition:'outEnd',
      dataLabelFormatCode:'0.0"%"',dataLabelColor:P.ink,dataLabelBkgrdColor:P.bg,dataLabelFontSize:13.0,
      showLegend:true,legendPos:'b',legendColor:P.muted,legendFontSize:13,
      showBorder:false,showCatName:false,showSerName:false,
      catAxisLabelColor:P.ink,catAxisLabelFontSize:15.5,catAxisLabelFontFace:'Arial',catAxisLineShow:false,
      valAxisLabelColor:P.muted,valAxisLabelFontSize:11,valAxisMinVal:0,valAxisMaxVal:110,valAxisMajorUnit:25,valAxisLineShow:false,
      valAxisLabelFormatCode:'0"%"',catGridLine:{style:'none'},valGridLine:{color:'294749',width:.6},
      chartArea:{fill:{color:'0B252B',transparency:100},border:{color:'0B252B',pt:0}},
      plotArea:{fill:{color:'0B252B',transparency:100},border:{color:'0B252B',pt:0}},
      showShadow:false,showMarker:false,barGapWidthPct:115,layout:{x:.08,y:.11,w:.86,h:.60},
    },'chart'));
  });
  group('error_table',.47,()=>{
    panel(8.68,2.25,3.97,4.02);
    text('TEST-ROW ERRORS',8.97,2.57,3.36,.20,11.3,{color:P.muted,charSpacing:1.1,bold:true});
    text('Logistic',10.10,3.15,1.08,.22,12.8,{bold:true,color:P.mint,align:'center'});
    text('Rain-only',11.36,3.15,1.01,.22,12.8,{bold:true,color:P.amber,align:'center'});
    text('False\npositives',8.96,3.76,1.22,.61,16.3,{color:P.muted});
    text('40',10.12,3.70,1.06,.68,42,{bold:true,color:P.coral,align:'center'});
    text('8',11.41,3.70,.92,.68,42,{bold:true,align:'center'});
    text('Missed\npositives',8.96,4.84,1.22,.61,16.3,{color:P.muted});
    text('0',10.12,4.76,1.06,.68,42,{bold:true,align:'center'});
    text('12',11.35,4.76,1.09,.68,42,{bold:true,color:P.amber,align:'center'});
    text('138 rows / 4 test storms',8.97,5.80,3.36,.23,13.3,{color:P.muted});
  });
  group('promotion_decision',.69,()=>{
    text('Candidate remains unpromoted: it flags every test row.',.89,6.53,11.48,.36,21.3,{bold:true,color:P.mint});
  });
  notes('The candidate’s perfect synthetic recall comes with an unacceptable false-positive burden for promotion.',
    'At the validation-selected 0.3 threshold, the logistic candidate flags all 138 test rows: 98 true positives, 40 false positives, zero true negatives and zero missed positives. Recall is 1.0 and precision 0.7101. The separate 75 mm rainfall-only comparator has 86 true positives, 32 true negatives, eight false positives and 12 misses: recall 0.8776 and precision 0.9149. The rainfall-only comparator is not the composite rule running in the map. These correlated rows are decision opportunities, not distinct delivered messages or independent storms. Four synthetic test storms cannot support stable calibration, metric intervals, city-level accuracy or model promotion. The running application never loads the candidate for decisions.',
    'outputs/evidence/evaluation.json; docs/MODEL_CARD.md; docs/PROJECT_REPORT.md, Baseline and separate model experiment.','50 seconds');

  // 14 — Failure behavior is legible, with actual outage geography.
  header('Failure handling','Unknown data stays visibly unknown.',
    'The outage scenario preserves original issue times instead of refreshing stale evidence.','warning');
  group('outage_explanation',.15,()=>{
    stat('9 / 9','cells become Unknown\nduring the recorded feed outage',.80,2.42,3.95,P.muted);
    miniCard('CloudOff','Feed outage','No invented observations\nand no zero-rain substitution',.66,4.61,4.24,1.84,'coral');
  });
  group('outage_capture',.36,()=>{
    panel(5.31,2.31,7.33,4.57);image('outage_map',5.47,2.47,7.01,4.23);
  },'float');
  notes('The tested outage path represents missing support honestly and suppresses stale actions.',
    'The moderator’s Feed outage control advances demo time by 105 minutes without inserting rainfall. All nine cells become Unknown with null current indices, and previous issue times are retained. Stale or expired evidence stops queued alert delivery. Recover feed advances synthetic time by 15 minutes and reconstructs a clearly labelled synthetic history; it does not pretend missing observations from a real outage were recovered. The backend suite also injects a worker inference failure, logs its class, rolls back related writes, and verifies recovery without duplicate decisions.',
    '.impeccable/review/feed-outage-dark.png; outputs/evidence/browser-acceptance.json; docs/ACCEPTANCE.md; docs/DEMO_RUNBOOK.md.','35 seconds');

  // 15 — Recorded evidence, dates and local measurement scope.
  header('Recorded acceptance','The delivery is backed by inspectable checks.',
    'Acceptance evidence for the synthetic v0.1.1 release, recorded 11 November 2026.','data');
  const checks=[['44','backend tests','ShieldCheck'],['14','browser workflows','Map'],['7','Windows launcher\nchecks','CodeXml'],['62','captured UI states','Eye']];
  checks.forEach((q,i)=>group(`check_${i}`,.15+i*.11,()=>{
    const x=.66+i*3.06;panel(x,2.35,2.82,2.20);icon(q[2],x+2.05,2.65,.38);
    text(q[0],x+.23,2.74,1.73,.92,61,{bold:true,color:P.mint,charSpacing:-1.7});
    text(q[1],x+.25,3.86,2.32,.32,15.8,{color:P.muted});
  },'float'));
  group('acceptance_context',.61,()=>{
    panel(.66,4.90,5.82,1.89);icon('Users',.94,5.19,.38);
    text('Light + Dark / phone to desktop',1.53,5.20,4.61,.32,20.1,{bold:true});
    text('320–1440 px captures, keyboard flows, consent,\nmoderation, routes, outage and recovery.',.94,5.87,5.24,.53,16.5,{color:P.muted});
    panel(6.83,4.90,5.82,1.89);icon('Activity',7.11,5.19,.40);
    text(`Local dashboard p95: ${performance.p95_ms.toFixed(2)} ms`,7.70,5.20,4.58,.32,20.1,{bold:true});
    text('10 clients / 20 loopback requests / SQLite.\nFresh Linux CI passes the automated workflow.',7.11,5.87,5.25,.53,16.5,{color:P.muted});
  });
  notes('Recorded software acceptance covers functional and failure paths, with transparent performance scope.',
    'Report these as recorded results dated 11 November 2026, not as tests newly executed while creating the slides: 44 backend tests, 14 browser flow checks, seven isolated Windows launcher checks and 62 screenshots across Light and Dark at 1440, 1024, 390 and 320 pixel widths. Browser acceptance records no uncaught JavaScript errors or horizontal overflow. Device/System appearance, persistence and AA text/control contrast are checked. The local p95 is 57.42 milliseconds and median 41.955 milliseconds for 20 dashboard requests from ten concurrent loopback clients using SQLite; upstream latency and city-scale load are outside this measurement. The recorded fresh Ubuntu CI installs dependencies and passes backend, production build and browser checks. Automated checks are not human usability studies.',
    'docs/ACCEPTANCE.md; outputs/evidence/backend-acceptance.json; browser-acceptance.json; launcher-acceptance.json; performance.json; github-actions.json.','45 seconds');

  // 16 — A usable demo handoff, with a clickable local URL.
  header('Presentation demo','A focused demo follows six actions.',
    'The same workflow can be shown live or explained using the preceding captures.');
  const demo=[['01','MapPinned','Inspect','Select an area and\ncheck its evidence.'],['02','Upload','Report','Submit time, location\nand an observation.'],['03','ShieldCheck','Verify','Review evidence and\nmatch a road segment.'],['04','Route','Reroute','Compare changed edges\nafter verification.'],['05','Bell','Subscribe','Opt in to a ward and\ninspect delivery history.'],['06','RefreshCw','Replay','Run heavy rain, outage\nand synthetic recovery.']];
  demo.forEach((q,i)=>group(`demo_${i}`,.16+i*.10,()=>{
    const x=.66+(i%3)*4.11,y=2.30+Math.floor(i/3)*2.06;panel(x,y,3.80,1.73);
    text(q[0],x+.24,y+.27,.70,.38,25.4,{bold:true,color:P.teal});icon(q[1],x+3.08,y+.30,.37);
    text(q[2],x+1.00,y+.28,1.97,.36,22,{bold:true});
    text(q[3],x+.25,y+.92,3.24,.54,16.7,{color:P.muted});
  },'float'));
  group('demo_launch',.83,()=>{
    pill('OPEN LOCAL DEMO',.69,6.70,2.18,P.mint,{hyperlink:{url:'http://127.0.0.1:8000'}});
    text('Launch start.bat beforehand. The console shows the selected address.',3.19,6.75,9.22,.23,14,{color:P.muted});
  });
  notes('The supplied demo runbook gives a reproducible six-person, ten-minute live workflow.',
    'If a live demo is included, pause the deck here. Launch start.bat from the project root before presenting; it opens the dashboard when ready, normally at http://127.0.0.1:8000, or the next available port. Use a separate rehearsal runtime to preserve normal data. The runbook’s proposed roles and timings are M1 scope/data 0:00–1:15; M2 GIS/route 1:15–2:30; M3 evaluation 2:30–4:00; M4 submission/privacy 4:00–5:30; M5 verification/reroute/mobile 5:30–7:00; M6 consent/alerts/failure replay 7:00–10:00. Use the displayed demo clock for observations. At Station, verify the north approach only when the submitted pin supports it. The moderator login in the local app is documented in the runbook. If time is short, describe the six actions using the preceding screenshots. The team labels are proposed responsibilities; named contributions are not yet supplied.',
    'docs/DEMO_RUNBOOK.md; README.md; docs/TEAM_CONTRIBUTIONS.md.','30 seconds, plus optional live demo');

  // 17 — Completion and future gates with real-world specificity.
  header('Next evidence gates','The path to a real pilot is clear.',
    'The synthetic software workflow is delivered. Real-world readiness needs its own evidence.');
  group('delivered_scope',.16,()=>{
    panel(.66,2.32,4.20,4.54);icon('CircleCheck',.96,2.62,.52);
    text('Delivered now',1.72,2.67,2.72,.35,23,{bold:true});
    const items=['Local map and area evidence','Private reports + moderation','Verified road exclusions','Consent-based alert lifecycle','Evaluation and release records'];
    items.forEach((q,i)=>{icon('Check',.99,3.56+i*.53,.24);text(q,1.48,3.54+i*.53,3.08,.29,15.5,{color:P.muted});});
    pill('SYNTHETIC DEMONSTRATION',.98,6.24,3.53);
  },'float');
  const gates=[['Globe','Choose a pilot and licensed inputs','Audit source access, coverage and time semantics.'],['Gauge','Validate with historical flood events','Use credible labels and separated held-out events.'],['Users','Run field and human reviews','GIS, usability, local language and team sign-offs.'],['Network','Accept the deployment environment','Test PostGIS, hosting and real notification delivery.']];
  gates.forEach((q,i)=>group(`gate_${i}`,.30+i*.12,()=>{
    const y=2.38+i*1.12;icon(q[0],5.32,y+.08,.43,i<2?'amber':'mint');
    text(q[1],6.03,y+.04,6.47,.32,19.7,{bold:true});
    text(q[2],6.03,y+.49,6.34,.31,15.9,{color:P.muted});
  }));
  notes('The next steps are evidence collection and validation gates, not unsupported claims of deployment readiness.',
    'The synthetic implementation closes the local software path. Real pilot selection and source/licence access remain open. Historical forecasting requires credible positive and negative event labels, receipt-time leakage checks, enough event-separated data and a frozen comparison at an acceptable alert burden. The team must complete named contributions, peer review and rehearsal. Field GIS review, five consenting human usability testers and a fluent local-language reviewer have not been recorded. The optional PostgreSQL/PostGIS adapter and container preparation are supplied but untested locally; hosting, real providers and multi-worker operation require separate acceptance.',
    'docs/REMAINING_TASKS.md; docs/PROJECT_STATUS.md; docs/MODEL_CARD.md; docs/TEAM_CONTRIBUTIONS.md.');

  // 18 — Closing, with an actual repository hyperlink.
  header('Takeaways','Visible evidence supports useful local decisions.','', 'hero');
  group('closing_claim',.17,()=>{
    text('FLOODLINE',.72,2.33,10.77,.95,64,{bold:true,color:P.ink,charSpacing:2.0});
    text('Trace the data. Review the observation. Explain the action.',.75,3.60,11.37,.49,24,{color:P.mint});
  },'float',.55);
  const takeaways=[['Database','Traceable inputs'],['ShieldCheck','Reviewed reports'],['Bell','Accountable actions']];
  takeaways.forEach((q,i)=>group(`takeaway_${i}`,.37+i*.10,()=>{
    const x=.74+i*4.08;panel(x,4.60,3.76,1.08);icon(q[0],x+.24,4.91,.40);text(q[1],x+.92,4.96,2.62,.31,18,{bold:true});
  },'float'));
  group('questions',.75,()=>{
    text('Questions & discussion',.77,6.28,5.70,.42,25,{bold:true});
    text('github.com/Godavenger/floodline-caa',7.18,6.46,5.27,.28,15.5,{color:P.muted,align:'right',hyperlink:{url:'https://github.com/Godavenger/floodline-caa'}});
  });
  notes('The delivered project’s value is a traceable local workflow, with honest limits.',
    'Close on three ideas: traceable data, reviewed community evidence and accountable actions. The platform demonstrates the complete local pipeline now, while explicitly leaving real forecasting validity and deployment approval to later evidence. Invite questions. If asked about accuracy, refer to slide 13 and its false-positive burden rather than quoting perfect recall alone. If asked about responsibilities or sources, the next two appendix slides provide backup. The repository link is clickable.',
    'docs/PROJECT_REPORT.md; docs/PROJECT_STATUS.md; https://github.com/Godavenger/floodline-caa.','25 seconds');

  // 19 — Proposed roles and concrete technical artifacts, without invented names.
  header('Appendix / technical handoffs','Six responsibility areas connect the stack.',
    'M1–M6 are proposed team labels from the pipeline; named contribution records remain to be completed.');
  const roles=[
    ['M1','Database','Data and sources','Python • provenance • quality checks'],
    ['M2','Compass','GIS and routing','Shapely • PyProj • NetworkX'],
    ['M3','SlidersHorizontal','Baseline and evaluation','Interpretable rule • scikit-learn'],
    ['M4','CodeXml','Backend and integration','FastAPI • SQLite • authenticated APIs'],
    ['M5','Map','Resident and moderator UI','React • TypeScript • Leaflet'],
    ['M6','Bell','Alerts and acceptance','Delivery state • tests • release evidence'],
  ];
  roles.forEach((q,i)=>group(`role_${i}`,.14+i*.08,()=>{
    const x=.66+(i%3)*4.11,y=2.31+Math.floor(i/3)*2.20;panel(x,y,3.80,1.83);
    pill(q[0],x+.25,y+.23,.67);icon(q[1],x+3.08,y+.28,.38);
    text(q[2],x+.26,y+.85,3.31,.34,18,{bold:true});
    text(q[3],x+.26,y+1.38,3.25,.28,13,{color:P.muted});
  }));
  notes('The implementation follows the proposed six-person module handoffs without inventing individual contributions.',
    'These labels come from the supplied pipeline and contribution template. Do not assign real people or claim hours, peer review or human usability results that have not been supplied. The delivered local architecture is Python/FastAPI and SQLite, React/TypeScript/Leaflet, Shapely/PyProj/NetworkX for GIS and scikit-learn for the separate experiment. PostgreSQL/PostGIS preparation exists as an optional path and is untested locally. Each member should be able to explain the entire data-to-action flow and one failure case, in addition to their proposed primary module.',
    'docs/TEAM_CONTRIBUTIONS.md; docs/ARCHITECTURE.md; outputs/Smart_City_Flood_Prediction_CAA_Pipeline.md.','Backup slide');

  // 20 — Supporting records and real links, distinct from future source candidates.
  header('Appendix / sources','Project requirements and evidence are linked.',
    'Project-authored synthetic fixtures supply this release’s data.');
  group('project_records',.14,()=>{
    panel(.66,2.31,5.82,4.55);icon('FileText',.94,2.62,.42);
    text('Project records',1.60,2.68,4.39,.33,22,{bold:true});
    const rows=[['Assignment','project description.docx, item 3'],['Implementation plan','Smart_City_Flood_Prediction_CAA_Pipeline.md'],['Release and limits','PROJECT_REPORT.md / MODEL_CARD.md'],['Measured evidence','evaluation.json / acceptance records'],['Data provenance','SOURCE_REGISTER.md / data/manifest.json']];
    rows.forEach((q,i)=>{const y=3.47+i*.60;text(q[0],.96,y,4.95,.24,15.7,{bold:true});text(q[1],.96,y+.31,5.11,.20,12.3,{color:P.muted});});
  });
  group('implementation_links',.32,()=>{
    panel(6.83,2.31,5.82,2.28);icon('BookOpen',7.10,2.62,.41);
    text('Implementation references',7.76,2.68,4.51,.31,21,{bold:true});
    const links=[['FastAPI','https://fastapi.tiangolo.com/'],['Leaflet','https://leafletjs.com/reference.html'],['scikit-learn','https://scikit-learn.org/stable/modules/model_evaluation.html'],['PostGIS','https://postgis.net/documentation/']];
    links.forEach((q,i)=>text(q[0],7.12+(i%2)*2.62,3.43+Math.floor(i/2)*.46,2.28,.27,17.2,{color:P.mint,hyperlink:{url:q[1]}}));
  });
  group('candidate_sources',.47,()=>{
    panel(6.83,4.92,5.82,1.94);icon('Globe',7.10,5.21,.41,'amber');
    text('Real-pilot candidates',7.76,5.25,4.45,.31,21,{bold:true});
    text('IMD • India-WRIS/CWC • NASA IMERG\nOpen-Meteo • municipal records • OSM',7.12,5.84,5.21,.54,17,{color:P.muted});
    text('Access and suitability remain unverified.',7.12,6.53,5.21,.22,13.1,{color:P.amber});
  });
  notes('The project evidence and implementation references are distinguishable from future real-data candidates.',
    'All environmental observations, event labels, wards and road geometry used by this release are project-authored synthetic fixtures. The assignment and pipeline define the scope. The source register records provenance, rights and candidate-source limitations. FastAPI, Leaflet, scikit-learn and PostGIS are implementation references, not evidence of flood-prediction accuracy. IMD, CWC/India-WRIS, NASA IMERG, Open-Meteo, municipalities and OSM are future candidates; their data has not been accessed or ingested in this release. Inspect access, licences, timestamp semantics, resolution and geographic relevance before accepting a real adapter. All displayed reference names on the implementation panel have clickable external links.',
    'docs/SOURCE_REGISTER.md; docs/PROJECT_REPORT.md, Reference starting points; THIRD_PARTY.md; data/manifest.json.','Backup slide');

  fs.writeFileSync(path.join(__dirname,'animation_plan.json'),JSON.stringify(animationPlan,null,2));
  fs.writeFileSync(path.join(__dirname,'content_manifest.json'),JSON.stringify(contentManifest,null,2));
  fs.writeFileSync(path.join(__dirname,'layout_manifest.json'),JSON.stringify(layoutManifest,null,2));
  await pptx.writeFile({fileName:path.join(__dirname,'Floodline_Static_Base.pptx'),compression:true});
  console.log(`Created ${animationPlan.length} slides, native chart, ${contentManifest.length} speaker notes, and animation plan.`);
}
build().catch(e=>{console.error(e);process.exit(1);});
