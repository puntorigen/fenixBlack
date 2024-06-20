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

function ServiceExample_JobSearch() {
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
            // this example, requests a PDF with a resume and a country name
            // researches the best available jobs for that resume in that country
            // and writes an email for each job offer, and returns the emails
            // api=true generates an API endpoint for this service
            // .start(settings) starts the service with the given settings (optional, API keys, etc)
            let emails = await service.current.start({});
            // you can use the emails[] here to send them from the user's email
          }}
        >Start Service</WiredButton>
        <Service ref={service} api={true} flow="resume->country->resume_summary->found_jobs->emails" onFinish={()=>{}}>
            <InputPDF showDrop={true} schema={resumeSchema} name="resume" hint="Drop your PDF resume here" /> {/* the schema (zod) enforces the extraction output */}
            <InputField name="country" hint="Enter the country name where you want to work" />
            <Meeting name="resume_summary" task="review the {resume}, determine the resume language, enumerate the most important skills and create a summary suitable for comparing it with a JD offer tailored for {country}">
                <ResearchAnalyst name="Pedro" />
            </Meeting>
            <Meeting name="found_jobs" schema={found_jobs} task="search jobs in {country} for a professional {resume_summary}">
                <ResearchAnalyst name="Pedro" />
                <Reviewer name="Leo" task="Double checks that the job offers are a good match for the {resume}." />
            </Meeting>
            <Meeting name="emails" schema={emails} task="write an email for every item on {found_jobs}, as if it was written by {resume.full_name} for applying to each position.">
                <ResearchAnalyst name="Pedro" />
                <EmailWritter name="Juan"/>
            </Meeting>
        </Service>
      </>
  );
}

export default ServiceExample_JobSearch;
