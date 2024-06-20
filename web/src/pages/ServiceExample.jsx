import React, { useRef, useState } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';
import { tools } from './experts/constants';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Designer from '../experts/Designer';
import Lawyer from '../experts/Lawyer';
import ResearchAnalyst from '../experts/ResearchAnalyst';
import LeadMarketAnalyst from '../experts/Marketing/LeadMarketAnalyst';

function ServiceExample() {
  const meetingBrand = useRef(null);
  const meetingPrivacy = useRef(null);
  const [testTask, setTestTask] = useState('Create brand guidelines for www.enecon.com');
  const [inMeeting, setInMeeting] = useState(false);
  const [dialog, setDialog] = useState([]);
  return (
      <>
        <WiredButton 
          style={{marginTop:20, color:'yellowgreen' }}
          onClick={async()=>{ 
            let info = await service.current.start("brandBuilder","for www.xx.com",brandSchema);
            /* ask the user to choose a product, or use the first one
             brochure = await service.current.start("brochure", 
                  `using the {brand} information, design a 1 page PDF brochure for product ${info.products[0].name}`,
                  brochureSchema
            );*/
            await meetingPrivacy.current.start(
                testTask,
                privacyPolicy);
          }}
        >Start Service</WiredButton>
        <Service industry="marketing" ref={service} flow="brandBuilder->brochure->brochurePDF" onFinish={()=>{}}>
          <WhiteBoard type={"thought"} for="single|all" ref={thinkingBoard}/> // shows a mindmap of the whole factory progress
          <Meeting name="brandBuilder" ref={meetingBrand} task="research the products, services and build the design brand guidelines" outputKey="brand">
              <WhiteBoard type={"output"} /> //shows a mindmap of the overall work output
              <AccountManager age={37} gender={"male"} name={"Mauricio"} />
              <Designer gender={"female"} name={"Marta"} />
          </Meeting>
          <Meeting name="brochure" ref={meetingBrochure} task="Create the material for a PDF brochure" outputKey="brochure">
              <AccountManager name={"Mauricio"} /> //each 'name' has memory context history
              <PrintDesigner gender={"male"} name={"Christian"} /> // expert at creating designs for print
              <PDFBuilder gender={"male"} name={"Pablo"} /> // (dev like) expert at creating PDFs using weasyPrint in the back
              <Copywriter name={"Rodrigo"} />
              <ProductManager name={"Rodrigo"} />
              <Reviewer name={"Leo"} task={"Checks the brochure for errors in grammar, spelling, and punctuation."} />
          </Meeting>
          <BrochurePDF name="brochurePDF" ref={brochurePDF} output="" /> // this takes the result from the previous step as input, and creates the PDF file as base64
        </Service>
      </>
  );
}

export default ServiceExample;
