import React, { useRef, useState } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';
import { tools } from './experts/constants';
import { z } from 'zod';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Designer from '../experts/Designer';
import Lawyer from '../experts/Lawyer';
import ResearchAnalyst from '../experts/ResearchAnalyst';
import LeadMarketAnalyst from '../experts/Marketing/LeadMarketAnalyst';

function ServiceExample_Competitors() {
  const service = useRef(null);
  const [inMeeting, setInMeeting] = useState(false);
  const [dialog, setDialog] = useState([]);
  const resumeSchema = z.object({
    full_name: z.string().describe('The full name of the person'),
    email: z.string().email().describe('The email of the person if any'),
    phone: z.string().describe('The phone number of the person if any'),
    address: z.string().describe('The address of the person if any'),
    summary: z.string().describe('The summary of the person'),
    experience: z.array(z.object({
      company: z.string().describe('The company name'),
      title: z.string().describe('The title of the person'),
      start_date: z.string().describe('The start date of the person'),
      end_date: z.string().describe('The end date of the person'),
      description: z.string().describe('The description of the person'),
    })).describe('The experience of the person'),
  });
  const found_jobs = z.array(z.object({
    position_offered: z.string().describe('The position offered'),
    company: z.string().describe('The company name'),
    company_url: z.string().url().describe('The company URL'),
    company_email: z.string().email().describe('The company email'),
    offer_link: z.string().url().describe('The offer link'),
    match_resume_score: z.number().describe('The match resume score between the resume and the job offer, from 0 to 100'),
  }));
  const emails = z.array(z.object({
    to: z.string().email().describe('The email of the recipient'),
    subject: z.string().describe('The subject of the email'),
    body: z.string().describe('The body of the email'),
    job_offer: z.object({
        position_offered: z.string().describe('The position offered'),
        company: z.string().describe('The company name'),
        company_url: z.string().url().describe('The company URL'),
        company_email: z.string().email().describe('The company email'),
        offer_link: z.string().url().describe('The offer link'),
        match_resume_score: z.number().describe('The match resume score between the resume and the job offer, from 0 to 100'),
    }).describe('The job offer reference'),
  }));
  
  return (
      <>
        <WiredButton 
          style={{marginTop:20, color:'yellowgreen' }}
          onClick={async()=>{ 
            // this example, requests a customer's webpage url and builds a report with their competitors
            // - the service also generates a diagram of its own functionality for reference
            // - this can be shown using the prop showDiagram={true} on the Service component
            // .start(settings) starts the service with the given settings (optional, API keys, etc)
            // .start(settings,flags) flags => { api: true, showDiagram, etc }
            // flag download:true will trigger the download of the generated files
            // flag showDownload:true will show a download button for the generated files
            // the tool GeneratePDF is a special kind of meeting with predefined coordinated experts (inherits the previous context)
            let files = await service.current.start({},{ download:true });
          }}
        >Start Service</WiredButton>
        <Service ref={service} api={true} showDownload={true}>
            <InputField name="customer_url" type="url" hint="Enter the customer's webpage url"/>
            <Meeting name="customer_design_guidelines" task="extract design guidelines from {customer_url}">
                <ResearchAnalyst name="Pedro" />
                <Designer />
            </Meeting>
            <Meeting name="customers_products" task="analyze the customer's products, features and prices">
                <ResearchAnalyst name="Pedro" />
                <Reviewer />
            </Meeting>
            <Meeting name="competitors" task="search for posible product offering competitors, return links, titles, reasons">
                <ResearchAnalyst name="Pedro" />
                <Reviewer />
            </Meeting>
            <Meeting name="benchmark" task="create a benchmark between {customers_products} and {competitors}">
                <ResearchAnalyst name="Pedro" />
                <Designer />
            </Meeting>
            <GeneratePDF task="create a PDF report file with {benchmark}, highlighting the features of the customer's products on {customers_products}, using the brand styles defined on {customer_design_guidelines}"/>
        </Service>
      </>
  );
}

export default ServiceExample_Competitors;
