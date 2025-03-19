import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: 'NCAudioRecorderNode',
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
                const startBtn = document.createElement("div");
                startBtn.textContent = "";
                startBtn.classList.add("comfy-nc-big-button");

                const countdownDisplay = document.createElement("div");
                countdownDisplay.classList.add("comfy-nc-value-small-display");

                // Add the button and tag to the node using addDOMWidget
                this.addDOMWidget("button_widget", "Press and Hold to Record", startBtn);
                this.addDOMWidget("text_widget", "Countdown Display", countdownDisplay);


                // Retrieve settings from widgets
                const recordModeWidget = currentNode.widgets.find(w => w.name === 'record_mode');
                const newGenerationWidget = currentNode.widgets.find(w => w.name === 'new_generation_after_recording');


                if (recordModeWidget) {
                    recordModeWidget.callback = (value) => {
                        switchButtonMode(recordModeWidget.value);
                        // Save the current record mode to localStorage
                        localStorage.setItem('nc_audio_recorder_record_mode', recordModeWidget.value);
                    };
                }

                const switchButtonMode = (mode) => {
                    if (mode === 'press_and_hold') {
                        startBtn.innerText = isRecording ? 'Recording...' : 'Press and Hold to Record';
                        startBtn.onmousedown = startRecording;
                        startBtn.onmouseup = () => stopRecording(true); // manual stop
                        startBtn.onmouseleave = () => stopRecording(true); // manual stop
                        startBtn.onclick = null;
                    } else if (mode === 'start_and_stop') {
                        if (isRecording) {
                            startBtn.innerText = 'STOP';
                        } else {
                            startBtn.innerText = 'START';
                        }
                        startBtn.onmousedown = null;
                        startBtn.onmouseup = null;
                        startBtn.onmouseleave = null;
                        startBtn.onclick = () => {
                            if (isRecording) {
                                stopRecording(true); // manual stop
                            } else {
                                startRecording();
                            }
                        };
                    }
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

                                    // Trigger a new queue job if `new_generation_after_recording` is enabled
                                    if (newGenerationWidget && newGenerationWidget.value === true) {
                                        // Locate the div container that holds the activation button
                                        const buttonContainer = document.querySelector('div[data-testid="queue-button"]');

                                        if (buttonContainer) {
                                            
                                            const queueButton = buttonContainer.querySelector('button[data-pc-name="pcbutton"]');
                                            if (queueButton) {
                                                queueButton.click();
                                                console.log('New queue generation triggered.');
                                            } else {
                                                console.warn("Queue button not found inside container.");
                                            }
                                        } else {
                                            console.warn("Queue button container not found.");
                                        }
                                    }

                                };
                                reader.readAsDataURL(audioBlob);
                            };
                            mediaRecorder.start();

                            switchButtonMode(recordModeWidget.value);

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

                        countdownDisplay.textContent = ''; // Clear countdown display

                        switchButtonMode(recordModeWidget.value);
                    }
                };

                // Initialize button mode based on the record mode
                // Load settings from localStorage if available
                const savedRecordMode = localStorage.getItem('nc_audio_recorder_record_mode');
                if (savedRecordMode) {
                    recordModeWidget.value = savedRecordMode;
                }
                switchButtonMode(recordModeWidget.value);

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
    .comfy-nc-big-button {
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

    .comfy-nc-big-button:hover {
        background-color: #45a049;
    }

    .comfy-nc-big-button:active {
        background-color: #3e8e41;
    }

    .comfy-nc-value-display {
        margin-top: 20px;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
    }
    
    .comfy-nc-value-small-display {
        margin-top: 20px;
        font-size: 14px;
        text-align: center;
    }
`;
document.head.appendChild(style);