import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: 'NCNodes.AudioRecorder',
    async getCustomWidgets(app) 
    {
        return {
            AUDIOINPUTMIX(node, inputName, inputData, app) {
                const widget = {
                    type: inputData[0],
                    name: inputName,
                    size: [128, 32],
                    draw(ctx, node, width, y) {},
                    computeSize(...args) {
                        return [128, 32]; // Default widget size
                    },
                };
                node.addCustomWidget(widget);
                return widget;
            },
        };
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass === 'NCAudioRecorderNode') {
            nodeData.input.required.audioUI = ["AUDIO_UI"];

            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const currentNode = this;

                let mediaRecorder;
                let audioChunks = [];
                let isRecording = false;
                let recordingTimer;

                // Hide the base64_data widget
                const base64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                if (base64Widget) {
                    base64Widget.type = "hidden";
                }

                // Create a custom button element
                const recordBtn = document.createElement("div");
                recordBtn.textContent = "";
                recordBtn.classList.add("recordButton");

                const countdownDisplay = document.createElement("div");
                countdownDisplay.classList.add("countdownDisplay");

                // Add the button and tag to the node using addDOMWidget
                this.addDOMWidget("button_widget", "RECORD", recordBtn);
                this.addDOMWidget("text_widget", "Countdown Display", countdownDisplay);

                const switchButtonText = () => {
                        if (isRecording) {
                            recordBtn.innerText = 'STOP';
                        } else {
                            recordBtn.innerText = 'RECORD';
                        }
                        recordBtn.onmousedown = null;
                        recordBtn.onmouseup = null;
                        recordBtn.onmouseleave = null;
                        recordBtn.onclick = () => {
                            if (isRecording) {
                                stopRecording(true); // manual stop
                            } else {
                                startRecording();
                            }
                        };
                };

                const startRecording = () => {
                    if (isRecording) {
                        return; // Don't start a new recording if we're not supposed to continue the loop
                    }

                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        console.error('Browser does not support audio recording');
                        return;
                    }

                    audioChunks = [];
                    isRecording = true;
                    recordBtn.classList.replace('recordButton', 'recordButtonRecording');

                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then((stream) => {
                            mediaRecorder = new MediaRecorder(stream, {
                                mimeType: 'audio/webm'
                            });
                            mediaRecorder.ondataavailable = (event) => {
                                if (event.data.size > 0) {
                                    audioChunks.push(event.data);
                                }
                            };
                            mediaRecorder.onstop = () => {
                                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                                const reader = new FileReader();

                                reader.onloadend = () => {
                                    const base64data = reader.result.split(',')[1];
                                    const audioBase64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                                    if (audioBase64Widget) {
                                        audioBase64Widget.value = base64data;
                                    }

                                    const audioUIWidget = currentNode.widgets.find(w => w.name === "audioUI");
                                    if (audioUIWidget) {
                                        audioUIWidget.element.src = `data:audio/webm;base64,${base64data}`;
                                        audioUIWidget.element.classList.remove("empty-audio-widget");
                                    }

                                    console.log('Audio recording saved.');

                                };
                                reader.readAsDataURL(audioBlob);
                            };
                            mediaRecorder.start();

                            switchButtonText();

                            console.log('Recording started...');

                            // Start the countdown for maximum recording duration
                            const recordDurationMaxWidget = currentNode.widgets.find(w => w.name === 'record_duration_max');
                            const maxDuration = recordDurationMaxWidget ? recordDurationMaxWidget.value : 10;
                            
                            let remainingTime = maxDuration;
                            const startCountdown = Math.min(10, maxDuration);

                            const updateCountdown = () => {
                                if (remainingTime <= startCountdown) {
                                    countdownDisplay.textContent = `Recording will stop in ${remainingTime} seconds`;
                                } else {
                                    countdownDisplay.textContent = 'Recording...';
                                }
                                
                                if (remainingTime <= 0) {
                                    clearInterval(recordingTimer);
                                    remainingTime = 0;
                                    if (isRecording) {
                                        stopRecording(false); //auto stop
                                    }
                                }
                                remainingTime--;
                            };

                            // execute immediately
                            updateCountdown();
                            // start timer
                            recordingTimer = setInterval(updateCountdown, 1000);
                        })
                        .catch(error => console.error('Error accessing audio devices.', error));
                };

                const stopRecording = (isManualStop = false, delay = 300) => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        setTimeout(() => {
                            if (mediaRecorder) {
                                mediaRecorder.stop();
                            }
                            mediaRecorder = null;
                        }, delay);
                        isRecording = false;

                        if (recordingTimer) {
                            clearInterval(recordingTimer);
                            recordingTimer = null;
                        }

                        recordBtn.classList.replace('recordButtonRecording', 'recordButton');

                        countdownDisplay.textContent = ''; // Clear countdown display

                        switchButtonText();
                    }
                };

                switchButtonText();

                const onRemoved = this.onRemoved;
                this.onRemoved = function () {
                    if (recordingTimer) {
                        clearInterval(recordingTimer);
                    }
                    return onRemoved?.();
                };

                this.serialize_widgets = true; // Ensure widget state is saved
            };
        }
    }
});

// Add custom styles for the button
const style = document.createElement("style");
style.textContent = `
    .recordButton {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 20px;
        height: 40px !important;
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s;
    }

    .recordButton:hover {
        background-color: #45a049;
    }

    .recordButton:active {
        background-color: #3e8e41;
    }

    .recordButtonRecording {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 20px;
        height: 40px !important;
        background-color: #af544c;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s;
    }

    .recordButtonRecording:hover {
        background-color: #a04e45;
    }

    .recordButtonRecording:active {
        background-color: #8e413e;
    }
    
    .countdownDisplay {
        margin-top: 20px;
        font-size: 14px;
        text-align: center;
    }
`;
document.head.appendChild(style);