import React, { useRef, useEffect, useCallback } from 'react';

const useRefs = () => {
    const refs = useRef({});

    const register = useCallback((refName, ref) => {
        refs.current[refName] = ref;
    }, []);

    const getRef = useCallback(refName => refs.current[refName], []);

    return [ refs, register ];
};

const Meeting = ({ children }) => {
    const [refs, register] = useRefs();

    useEffect(() => {
        // Log meta information from children
        const logMetaData = () => {
            console.log('refs', refs);
            Object.keys(refs.current).forEach(refName => {
                if (refs.current[refName] && refs.current[refName].meta) {
                    console.log(refs.current[refName].meta());
                }
            });
            /*childrenRefs.current.forEach(ref => {
                if (ref.current && ref.current.meta) {
                    console.log(ref.current.meta());
                }
            });*/
        };

        logMetaData();
    }, [children]); // Ensure it runs whenever children change
 
    const enhancedChildren = React.Children.map(children, (child, index) =>
        React.cloneElement(child, { ...child.props, ref: (ref)=>register(`field-${index}`,ref) })
    );

    return (
        <div>
            <h1>Meeting</h1>
            {enhancedChildren}
        </div>
    );
};

export default Meeting;
