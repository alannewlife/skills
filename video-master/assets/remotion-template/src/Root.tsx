import {Composition} from 'remotion';
import {SceneOneAdaptive} from './CompositionAdaptive';
import {TransitionAdaptive} from './TransitionAdaptive';
export const RemotionRoot=()=> <>
 <Composition id="SceneOneAdaptive" component={SceneOneAdaptive} width={1920} height={1080} fps={30} durationInFrames={626}/>
 <Composition id="TransitionAdaptive" component={TransitionAdaptive} width={1920} height={1080} fps={30} durationInFrames={240}/>
</>;
