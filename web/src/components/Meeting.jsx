import React, { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import { zodToJson } from '../utils/utils';

const useRefs = () => {
    const refs = useRef({});

    const register = useCallback((refName, ref) => {
        refs.current[refName] = ref;
    }, []);

    //const getRef = useCallback(refName => refs.current[refName], []);

    return [ refs, register ];
};

const Meeting = forwardRef(({ name, task, tools=[], outputKey, children }, refMain) => {
    const [refs, register] = useRefs();
    const [experts, setExperts] = useState({});

    useEffect(() => {
        // Log meta information from children
        const parseChildren = () => {
            Object.keys(refs.current).forEach(refName => {
                if (refs.current[refName] && refs.current[refName].meta) {
                    const meta = refs.current[refName].meta();
                    if (meta.type === 'expert') {
                        setExperts(prev => {
                            return { ...prev, [meta.name+'|'+meta.role]: meta };
                        })
                    }
                }
            });
        }
        parseChildren();
    }, []); // Ensure it runs whenever children change
 
    const enhancedChildren = React.Children.map(children, (child, index) =>
        React.cloneElement(child, { ...child.props, style:{ marginLeft: '20px' }, ref: (ref)=>register(`field-${index}`,ref) })
    );

    // Expose Meeting's methods to parent through ref
    useImperativeHandle(refMain, () => ({
        start: (context,schema)=>{
            // start meeting with given context, and zod output schema
            // 1. build a JSON of the meeting info + children JSON info + zod schema JSON
            let req = {
                meta: {
                    context, 
                    schema: zodToJson(schema),
                    name, task
                },
                experts
            };
            console.log('req',req);
            // 2. connect to backend via websocket and send data
            // 3. wait for responses and update the children with the new data
            // 4. wait for end of meeting, convert output JSON to zod schema and return, and assign raw output to outputKey ref variable
        },
        play: async()=>{
            // animate the meeting -> to test the experts
            const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
            Object.keys(refs.current).forEach(async(refName) => {
                if (refs.current[refName] && refs.current[refName].speak) {
                    await refs.current[refName].play('search');
                    await refs.current[refName].speak(`Hello, I am the ${refs.current[refName].meta().role}, and I'm here to help you with your task.`);
                    await sleep(4000);
                    await refs.current[refName].play('scrape');
                    await sleep(5000);
                    await refs.current[refName].avatarSize('100%');
                    await refs.current[refName].stop();
                    await sleep(5000);
                }
            }); 
        }
    }));

    return (
        <div>
            <h1 style={{ color:'#FFF'}}>Meeting</h1>
            {enhancedChildren}
        </div>
    );
});

export default Meeting;
